#!/usr/bin/env python3
"""
Service Manager for MCP Microservices
Manages lifecycle of all MCP services in the e-commerce system.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("service-manager")

@dataclass
class ServiceConfig:
    """Configuration for a single service."""
    name: str
    script_path: str
    port: Optional[int] = None
    instances: int = 1
    auto_restart: bool = True
    health_check_interval: int = 30
    dependencies: List[str] = None

@dataclass
class ServiceInstance:
    """Running instance of a service."""
    config: ServiceConfig
    process: subprocess.Popen
    instance_id: int
    start_time: datetime
    status: str = "running"
    last_health_check: Optional[datetime] = None

class ServiceManager:
    """Manages multiple MCP microservices."""
    
    def __init__(self, config_file: str = "services_config.json"):
        self.config_file = config_file
        self.services: Dict[str, ServiceConfig] = {}
        self.running_instances: Dict[str, List[ServiceInstance]] = {}
        self.shutdown_requested = False
        
        # Load service configurations
        self.load_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def load_config(self):
        """Load service configurations from file."""
        default_config = {
            "services": {
                "product-service": {
                    "script": "services/product_mcp_service.py",
                    "instances": 1,
                    "auto_restart": True
                },
                "recommendation-service": {
                    "script": "services/recommendation_mcp_service.py", 
                    "instances": 1,
                    "auto_restart": True
                },
                "order-service": {
                    "script": "services/order_mcp_service.py",
                    "instances": 1,
                    "auto_restart": True
                }
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                config_data = default_config
                logger.info(f"Created default configuration file: {self.config_file}")
            
            # Parse configurations
            for service_name, service_config in config_data.get("services", {}).items():
                self.services[service_name] = ServiceConfig(
                    name=service_name,
                    script_path=service_config["script"],
                    port=service_config.get("port"),
                    instances=service_config.get("instances", 1),
                    auto_restart=service_config.get("auto_restart", True),
                    health_check_interval=service_config.get("health_check_interval", 30),
                    dependencies=service_config.get("dependencies", [])
                )
            
            logger.info(f"Loaded configuration for {len(self.services)} services")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
    
    async def start_service(self, service_name: str) -> bool:
        """Start a service with all its instances."""
        if service_name not in self.services:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        config = self.services[service_name]
        logger.info(f"Starting service: {service_name} ({config.instances} instances)")
        
        # Check dependencies
        if config.dependencies:
            for dep in config.dependencies:
                if dep not in self.running_instances or not self.running_instances[dep]:
                    logger.error(f"Dependency {dep} not running for service {service_name}")
                    return False
        
        # Start instances
        instances = []
        for i in range(config.instances):
            try:
                # Get the project root directory (parent of orchestration)
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                script_full_path = os.path.join(project_root, config.script_path)
                
                # Start service process
                process = subprocess.Popen(
                    ["uv", "run", "python", script_full_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=project_root
                )
                
                # Send initialization message to keep service alive
                init_msg = json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "service-manager", "version": "1.0.0"}
                    }
                }) + "\n"
                
                try:
                    process.stdin.write(init_msg.encode())
                    process.stdin.flush()
                except Exception as e:
                    logger.error(f"Failed to initialize service {service_name}: {e}")
                
                instance = ServiceInstance(
                    config=config,
                    process=process,
                    instance_id=i,
                    start_time=datetime.now()
                )
                
                instances.append(instance)
                logger.info(f"Started {service_name} instance {i} (PID: {process.pid})")
                
                # Wait a moment to ensure it started properly
                await asyncio.sleep(1)
                
                if process.poll() is not None:
                    logger.error(f"Service {service_name} instance {i} failed to start")
                    return False
                
            except Exception as e:
                logger.error(f"Failed to start {service_name} instance {i}: {e}")
                return False
        
        self.running_instances[service_name] = instances
        logger.info(f"Successfully started {service_name} with {len(instances)} instances")
        return True
    
    async def stop_service(self, service_name: str) -> bool:
        """Stop a service and all its instances."""
        if service_name not in self.running_instances:
            logger.warning(f"Service {service_name} is not running")
            return True
        
        logger.info(f"Stopping service: {service_name}")
        
        instances = self.running_instances[service_name]
        for instance in instances:
            try:
                # Send SIGTERM first
                instance.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process(instance.process)),
                        timeout=10.0
                    )
                    logger.info(f"Gracefully stopped {service_name} instance {instance.instance_id}")
                except asyncio.TimeoutError:
                    # Force kill if needed
                    instance.process.kill()
                    logger.warning(f"Force killed {service_name} instance {instance.instance_id}")
                
            except Exception as e:
                logger.error(f"Error stopping {service_name} instance {instance.instance_id}: {e}")
        
        del self.running_instances[service_name]
        logger.info(f"Stopped service: {service_name}")
        return True
    
    async def _wait_for_process(self, process: subprocess.Popen):
        """Wait for a process to terminate."""
        while process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a service."""
        logger.info(f"Restarting service: {service_name}")
        
        # Stop first
        await self.stop_service(service_name)
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Start again
        return await self.start_service(service_name)
    
    async def health_check_service(self, service_name: str) -> Dict:
        """Perform health check on a service."""
        if service_name not in self.running_instances:
            return {"status": "not_running", "instances": 0}
        
        instances = self.running_instances[service_name]
        healthy_instances = 0
        total_instances = len(instances)
        
        for instance in instances:
            if instance.process.poll() is None:  # Process is still running
                try:
                    # Send health check request
                    health_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "health_check",
                            "arguments": {}
                        }
                    }
                    
                    # Note: This is a simplified health check
                    # In a real implementation, you might want to:
                    # 1. Send the request to stdin
                    # 2. Read response from stdout
                    # 3. Parse the JSON response
                    # For now, we just check if the process is alive
                    
                    healthy_instances += 1
                    instance.last_health_check = datetime.now()
                    instance.status = "healthy"
                    
                except Exception as e:
                    logger.warning(f"Health check failed for {service_name} instance {instance.instance_id}: {e}")
                    instance.status = "unhealthy"
            else:
                instance.status = "dead"
                logger.error(f"Service {service_name} instance {instance.instance_id} is dead")
        
        return {
            "status": "healthy" if healthy_instances == total_instances else "degraded",
            "healthy_instances": healthy_instances,
            "total_instances": total_instances,
            "last_check": datetime.now().isoformat()
        }
    
    async def monitor_services(self):
        """Continuously monitor service health."""
        logger.info("Starting service monitoring...")
        
        while not self.shutdown_requested:
            try:
                for service_name in self.services.keys():
                    if service_name in self.running_instances:
                        health = await self.health_check_service(service_name)
                        
                        if health["status"] == "degraded":
                            logger.warning(f"Service {service_name} is degraded: {health}")
                            
                            # Auto-restart if configured
                            config = self.services[service_name]
                            if config.auto_restart:
                                logger.info(f"Auto-restarting degraded service: {service_name}")
                                await self.restart_service(service_name)
                
                # Wait before next health check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error during service monitoring: {e}")
                await asyncio.sleep(5)
    
    async def start_all_services(self):
        """Start all configured services."""
        logger.info("Starting all services...")
        
        # Sort services by dependencies (simplified - assumes no circular deps)
        service_order = []
        remaining_services = set(self.services.keys())
        
        while remaining_services:
            for service_name in list(remaining_services):
                config = self.services[service_name]
                if not config.dependencies or all(dep in service_order for dep in config.dependencies):
                    service_order.append(service_name)
                    remaining_services.remove(service_name)
                    break
            else:
                # If we can't resolve dependencies, just start remaining services
                service_order.extend(remaining_services)
                break
        
        # Start services in order
        for service_name in service_order:
            success = await self.start_service(service_name)
            if not success:
                logger.error(f"Failed to start {service_name}, stopping startup process")
                return False
        
        logger.info("All services started successfully")
        return True
    
    async def stop_all_services(self):
        """Stop all running services."""
        logger.info("Stopping all services...")
        
        # Stop in reverse order
        service_order = list(self.running_instances.keys())
        service_order.reverse()
        
        for service_name in service_order:
            await self.stop_service(service_name)
        
        logger.info("All services stopped")
    
    def get_service_status(self) -> Dict:
        """Get status of all services."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        for service_name, config in self.services.items():
            if service_name in self.running_instances:
                instances = self.running_instances[service_name]
                running_count = sum(1 for i in instances if i.process.poll() is None)
                
                status["services"][service_name] = {
                    "configured_instances": config.instances,
                    "running_instances": running_count,
                    "status": "running" if running_count > 0 else "stopped",
                    "auto_restart": config.auto_restart
                }
            else:
                status["services"][service_name] = {
                    "configured_instances": config.instances,
                    "running_instances": 0,
                    "status": "stopped",
                    "auto_restart": config.auto_restart
                }
        
        return status
    
    async def run(self):
        """Main service manager loop."""
        logger.info("🚀 Starting MCP Service Manager...")
        
        try:
            # Start all services
            if not await self.start_all_services():
                logger.error("Failed to start all services")
                return
            
            # Start monitoring
            monitor_task = asyncio.create_task(self.monitor_services())
            
            # Wait for shutdown signal
            while not self.shutdown_requested:
                await asyncio.sleep(1)
            
            # Cancel monitoring
            monitor_task.cancel()
            
            # Stop all services
            await self.stop_all_services()
            
        except Exception as e:
            logger.error(f"Service manager error: {e}")
        finally:
            logger.info("🛑 Service Manager shutting down")

async def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        manager = ServiceManager()
        
        if command == "start":
            await manager.start_all_services()
            print("All services started")
        elif command == "stop":
            await manager.stop_all_services()
            print("All services stopped")
        elif command == "status":
            status = manager.get_service_status()
            print(json.dumps(status, indent=2))
        elif command == "restart":
            service_name = sys.argv[2] if len(sys.argv) > 2 else None
            if service_name:
                await manager.restart_service(service_name)
                print(f"Service {service_name} restarted")
            else:
                await manager.stop_all_services()
                await manager.start_all_services()
                print("All services restarted")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: start, stop, status, restart")
    else:
        # Run in daemon mode
        manager = ServiceManager()
        await manager.run()

if __name__ == "__main__":
    asyncio.run(main())

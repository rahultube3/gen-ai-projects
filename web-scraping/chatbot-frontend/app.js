// Wikipedia RAG Chatbot AngularJS Application
(function() {
    'use strict';

    // Create AngularJS module
    angular.module('wikipediaRAGChatbot', [])
        .controller('ChatbotController', ChatbotController);

    ChatbotController.$inject = ['$http', '$timeout', '$scope'];

    function ChatbotController($http, $timeout, $scope) {
        const vm = this;
        
        // Configuration
        vm.apiBaseUrl = 'http://localhost:8000';
        
        // Data properties
        vm.messages = [];
        vm.currentMessage = '';
        vm.isLoading = false;
        vm.systemStatus = {};
        vm.collectionInfo = { document_count: 0, sample_pages: [] };
        vm.sampleQueries = [];
        vm.newPageUrl = '';
        vm.isAddingPage = false;
        vm.addPageMessage = '';
        vm.addPageSuccess = false;

        // Initialize the application
        vm.init = function() {
            console.log('🚀 Initializing Wikipedia RAG Chatbot...');
            vm.refreshStatus();
            vm.loadSampleQueries();
            vm.addWelcomeMessage();
        };

        // Add welcome message
        vm.addWelcomeMessage = function() {
            vm.messages.push({
                type: 'bot',
                content: 'Hello! I\'m your Wikipedia RAG Chatbot. Add Wikipedia pages to my knowledge base and I\'ll help answer questions about them using AI-powered search and reasoning.',
                timestamp: vm.getCurrentTime(),
                sources: [],
                confidence: 0
            });
        };

        // Refresh system status
        vm.refreshStatus = function() {
            $http.get(vm.apiBaseUrl + '/health')
                .then(function(response) {
                    vm.systemStatus = response.data;
                    console.log('📊 System status:', vm.systemStatus);
                    vm.loadCollectionInfo();
                })
                .catch(function(error) {
                    console.error('❌ Error getting system status:', error);
                    vm.systemStatus = { status: 'error' };
                });
        };

        // Load collection information
        vm.loadCollectionInfo = function() {
            $http.get(vm.apiBaseUrl + '/collections')
                .then(function(response) {
                    if (response.data && response.data.length > 0) {
                        vm.collectionInfo = response.data[0];
                    }
                    console.log('📚 Collection info:', vm.collectionInfo);
                })
                .catch(function(error) {
                    console.error('❌ Error loading collections:', error);
                });
        };

        // Load sample queries
        vm.loadSampleQueries = function() {
            $http.get(vm.apiBaseUrl + '/sample-queries')
                .then(function(response) {
                    vm.sampleQueries = response.data || [];
                    console.log('💡 Sample queries loaded:', vm.sampleQueries.length);
                })
                .catch(function(error) {
                    console.error('❌ Error loading sample queries:', error);
                    // Fallback sample queries
                    vm.sampleQueries = [
                        'What is health data?',
                        'How does digital health work?',
                        'What are electronic health records?',
                        'Explain health informatics'
                    ];
                });
        };

        // Send message
        vm.sendMessage = function() {
            if (!vm.currentMessage || !vm.currentMessage.trim()) {
                return;
            }

            const userMessage = vm.currentMessage.trim();
            vm.currentMessage = '';
            
            // Add user message to chat
            vm.messages.push({
                type: 'user',
                content: userMessage,
                timestamp: vm.getCurrentTime()
            });

            // Add loading message
            const loadingMessageIndex = vm.messages.length;
            vm.messages.push({
                type: 'loading',
                content: 'Thinking...',
                timestamp: vm.getCurrentTime()
            });

            vm.isLoading = true;
            vm.scrollToBottom();

            // Send to API
            $http.post(vm.apiBaseUrl + '/chat', { 
                message: userMessage,
                timestamp: vm.getCurrentTime()
            })
            .then(function(response) {
                // Remove loading message
                vm.messages.splice(loadingMessageIndex, 1);
                
                // Add bot response
                vm.messages.push({
                    type: 'bot',
                    content: response.data.response,
                    timestamp: response.data.timestamp || vm.getCurrentTime(),
                    sources: response.data.sources || [],
                    confidence: response.data.confidence || 0
                });

                console.log('🤖 Bot response:', response.data);
            })
            .catch(function(error) {
                // Remove loading message
                vm.messages.splice(loadingMessageIndex, 1);
                
                // Add error message
                vm.messages.push({
                    type: 'bot',
                    content: 'Sorry, I encountered an error while processing your message. Please make sure the API server is running and try again.',
                    timestamp: vm.getCurrentTime(),
                    sources: [],
                    confidence: 0
                });

                console.error('❌ Chat error:', error);
            })
            .finally(function() {
                vm.isLoading = false;
                vm.scrollToBottom();
            });
        };

        // Send sample query
        vm.sendSampleQuery = function(query) {
            vm.currentMessage = query;
            vm.sendMessage();
        };

        // Add Wikipedia page
        vm.addWikipediaPage = function() {
            if (!vm.newPageUrl || !vm.newPageUrl.trim()) {
                return;
            }

            vm.isAddingPage = true;
            vm.addPageMessage = '';

            $http.post(vm.apiBaseUrl + '/add-page', {
                url: vm.newPageUrl.trim()
            })
            .then(function(response) {
                vm.addPageSuccess = response.data.success;
                vm.addPageMessage = response.data.message;
                
                if (response.data.success) {
                    vm.newPageUrl = '';
                    // Refresh collection info
                    $timeout(function() {
                        vm.loadCollectionInfo();
                    }, 1000);
                    
                    // Add confirmation message to chat
                    vm.messages.push({
                        type: 'bot',
                        content: `✅ Successfully added "${response.data.page_title}" to the knowledge base! You can now ask questions about this topic.`,
                        timestamp: vm.getCurrentTime(),
                        sources: [],
                        confidence: 0
                    });
                }

                console.log('📚 Add page result:', response.data);
            })
            .catch(function(error) {
                vm.addPageSuccess = false;
                vm.addPageMessage = 'Error adding page. Please check the URL and try again.';
                console.error('❌ Add page error:', error);
            })
            .finally(function() {
                vm.isAddingPage = false;
                vm.scrollToBottom();
                
                // Clear message after 5 seconds
                $timeout(function() {
                    vm.addPageMessage = '';
                }, 5000);
            });
        };

        // Clear chat
        vm.clearChat = function() {
            if (confirm('Are you sure you want to clear the chat history?')) {
                vm.messages = [];
                vm.addWelcomeMessage();
                console.log('🧹 Chat cleared');
            }
        };

        // Get current time formatted
        vm.getCurrentTime = function() {
            const now = new Date();
            return now.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit'
            });
        };

        // Scroll to bottom of chat
        vm.scrollToBottom = function() {
            $timeout(function() {
                const chatContainer = document.getElementById('chatContainer');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }, 100);
        };

        // Handle Enter key in chat input
        $scope.$on('$viewContentLoaded', function() {
            // Auto-focus on message input
            const messageInput = document.querySelector('input[ng-model="vm.currentMessage"]');
            if (messageInput) {
                messageInput.focus();
            }

            // Handle Enter key
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    const activeElement = document.activeElement;
                    if (activeElement && activeElement.tagName === 'INPUT' && 
                        activeElement.getAttribute('ng-model') === 'vm.currentMessage') {
                        event.preventDefault();
                        $scope.$apply(function() {
                            vm.sendMessage();
                        });
                    }
                }
            });
        });

        // API Health Check
        vm.checkApiHealth = function() {
            return $http.get(vm.apiBaseUrl + '/health')
                .then(function(response) {
                    return response.data.status === 'healthy';
                })
                .catch(function() {
                    return false;
                });
        };

        // Initialize on load
        vm.init();

        // Periodic status refresh
        setInterval(function() {
            $scope.$apply(function() {
                vm.refreshStatus();
            });
        }, 30000); // Every 30 seconds

        console.log('✅ Wikipedia RAG Chatbot Controller initialized');
    }
})();
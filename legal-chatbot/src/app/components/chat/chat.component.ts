import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { LegalRagService, ChatMessage } from '../../services/legal-rag.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit, AfterViewChecked, OnDestroy {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages: ChatMessage[] = [];
  currentMessage: string = '';
  isLoading: boolean = false;
  isConnected: boolean = false;
  showSettings: boolean = false;
  userRole: string = 'client';
  
  availableCategories: string[] = [];
  lastSearchInfo: any = null;
  
  suggestedQuestions: string[] = [
    'What are the requirements for forming a valid contract?',
    'What is at-will employment and what are the exceptions?',
    'What are the landlord obligations for habitability?',
    'What are Miranda rights in criminal proceedings?',
    'What is negligence in tort law?',
    'How does the Fair Housing Act protect tenants?'
  ];

  private messagesSubscription: Subscription = new Subscription();
  private shouldScrollToBottom: boolean = true;

  constructor(
    private legalRagService: LegalRagService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  ngOnInit(): void {
    // Only make HTTP requests in the browser, not during SSR
    if (isPlatformBrowser(this.platformId)) {
      this.checkConnection();
      this.loadCategories();
    }
    
    // Subscribe to messages
    this.messagesSubscription = this.legalRagService.messages$.subscribe(messages => {
      this.messages = messages;
      this.shouldScrollToBottom = true;
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  ngOnDestroy(): void {
    this.messagesSubscription.unsubscribe();
  }

  checkConnection(): void {
    this.legalRagService.getHealthStatus().subscribe({
      next: (response) => {
        this.isConnected = response.status === 'healthy';
      },
      error: (error) => {
        console.error('Connection check failed:', error);
        this.isConnected = false;
      }
    });
  }

  loadCategories(): void {
    this.legalRagService.getCategories().subscribe({
      next: (response) => {
        this.availableCategories = response.categories || [];
      },
      error: (error) => {
        console.error('Failed to load categories:', error);
      }
    });
  }

  sendMessage(): void {
    if (!this.currentMessage.trim() || this.isLoading) {
      return;
    }

    const userMessage = this.currentMessage.trim();
    this.legalRagService.addUserMessage(userMessage);
    
    // Clear input
    this.currentMessage = '';
    this.isLoading = true;

    // Add typing indicator
    const typingMessage = this.legalRagService.addTypingIndicator();

    // Search for legal documents
    this.legalRagService.searchDocuments(userMessage, this.userRole).subscribe({
      next: (response) => {
        // Remove typing indicator
        this.legalRagService.removeMessage(typingMessage.id);
        
        // Format and add assistant response
        const formattedResponse = this.legalRagService.formatLegalResponse(response);
        this.legalRagService.addAssistantMessage(formattedResponse);
        
        // Update search info
        this.lastSearchInfo = {
          total_results: response.total_results,
          duration: response.search_duration_seconds.toFixed(2),
          compliance_score: response.compliance_report?.compliance_score
        };
        
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Search failed:', error);
        
        // Remove typing indicator
        this.legalRagService.removeMessage(typingMessage.id);
        
        // Add error message
        this.legalRagService.addAssistantMessage(
          'I apologize, but I encountered an error while searching for legal information. Please check that the backend service is running and try again.'
        );
        
        this.isLoading = false;
      }
    });
  }

  selectSuggestion(question: string): void {
    this.currentMessage = question;
    this.sendMessage();
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  clearChat(): void {
    this.legalRagService.clearMessages();
    // Re-add welcome message
    this.legalRagService.addMessage({
      id: Date.now().toString(),
      content: 'Welcome to the Legal Document Assistant! I can help you search through legal documents and answer questions about various areas of law. How can I assist you today?',
      sender: 'assistant',
      timestamp: new Date()
    });
    this.lastSearchInfo = null;
  }

  toggleSettings(): void {
    this.showSettings = !this.showSettings;
  }

  formatMessage(content: string): string {
    // Convert markdown-style formatting to HTML
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
      .replace(/\n/g, '<br>') // Line breaks
      .replace(/• /g, '• ') // Bullet points
      .replace(/⚖️/g, '<span class="legal-icon">⚖️</span>') // Legal icon
      .replace(/⚠️/g, '<span class="warning-icon">⚠️</span>'); // Warning icon
    
    return formatted;
  }

  formatTime(timestamp: Date): string {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  trackByMessageId(index: number, message: ChatMessage): string {
    return message.id;
  }

  private scrollToBottom(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }
}

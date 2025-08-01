import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  isTyping?: boolean;
}

export interface SearchRequest {
  query: string;
  max_results?: number;
  user_role?: string;
  access_level?: string;
}

export interface SearchResponse {
  success: boolean;
  results: any[];
  compliance_report: any;
  search_allowed: boolean;
  total_results: number;
  search_duration_seconds: number;
  message: string;
}

export interface LegalDocument {
  id: string;
  title: string;
  text: string;
  category: string;
  jurisdiction: string;
  similarity: number;
  confidentiality_level: string;
  contains_pii: boolean;
  contains_privileged: boolean;
  compliance_checked: boolean;
  disclaimer_added: boolean;
  access_timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class LegalRagService {
  private readonly apiUrl = 'http://localhost:8000';
  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  constructor(private http: HttpClient) {
    // Add welcome message
    this.addMessage({
      id: this.generateId(),
      content: 'Welcome to the Legal Document Assistant! I can help you search through legal documents and answer questions about various areas of law including contracts, employment, housing, and more. How can I assist you today?',
      sender: 'assistant',
      timestamp: new Date()
    });
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  searchDocuments(query: string, userRole: string = 'client'): Observable<SearchResponse> {
    const searchRequest: SearchRequest = {
      query,
      max_results: 5,
      user_role: userRole,
      access_level: 'public'
    };

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.post<SearchResponse>(`${this.apiUrl}/search`, searchRequest, { headers })
      .pipe(
        catchError(error => {
          console.error('Search error:', error);
          throw error;
        })
      );
  }

  getHealthStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`).pipe(
      catchError(error => {
        console.error('Health check failed:', error);
        return of({ status: 'unhealthy', message: 'Backend not available' });
      })
    );
  }

  getCategories(): Observable<any> {
    return this.http.get(`${this.apiUrl}/categories`).pipe(
      catchError(error => {
        console.error('Error fetching categories:', error);
        // Return a default response if the backend is not available
        return of({ categories: [], total: 0 });
      })
    );
  }

  addMessage(message: ChatMessage): void {
    const currentMessages = this.messagesSubject.value;
    this.messagesSubject.next([...currentMessages, message]);
  }

  addUserMessage(content: string): void {
    this.addMessage({
      id: this.generateId(),
      content,
      sender: 'user',
      timestamp: new Date()
    });
  }

  addAssistantMessage(content: string): void {
    this.addMessage({
      id: this.generateId(),
      content,
      sender: 'assistant',
      timestamp: new Date()
    });
  }

  addTypingIndicator(): ChatMessage {
    const typingMessage: ChatMessage = {
      id: this.generateId(),
      content: '',
      sender: 'assistant',
      timestamp: new Date(),
      isTyping: true
    };
    this.addMessage(typingMessage);
    return typingMessage;
  }

  removeMessage(messageId: string): void {
    const currentMessages = this.messagesSubject.value;
    const updatedMessages = currentMessages.filter(msg => msg.id !== messageId);
    this.messagesSubject.next(updatedMessages);
  }

  clearMessages(): void {
    this.messagesSubject.next([]);
  }

  formatLegalResponse(searchResponse: SearchResponse): string {
    if (!searchResponse.success || !searchResponse.results.length) {
      return 'I couldn\'t find any relevant legal documents for your query. Please try rephrasing your question or ask about a different legal topic.';
    }

    let response = `Based on the legal documents I found, here's what I can tell you:\n\n`;
    
    // Add primary result
    const primaryResult = searchResponse.results[0] as LegalDocument;
    response += `**${primaryResult.title}** (${primaryResult.category})\n`;
    response += `${primaryResult.text}\n\n`;

    // Add additional relevant results if available
    if (searchResponse.results.length > 1) {
      response += `**Related Legal Information:**\n`;
      for (let i = 1; i < Math.min(3, searchResponse.results.length); i++) {
        const result = searchResponse.results[i] as LegalDocument;
        response += `• **${result.title}**: ${result.text.substring(0, 150)}...\n`;
      }
    }

    // Add compliance information
    if (searchResponse.compliance_report && !searchResponse.compliance_report.is_compliant) {
      response += `\n⚠️ **Compliance Notice**: This response has been reviewed for compliance and may have limitations.\n`;
    }

    // Add legal disclaimer
    response += `\n⚖️ **Legal Disclaimer**: This information is provided for general informational purposes only and does not constitute legal advice. The information may not reflect the most current legal developments and may not be applicable to your specific situation. For legal advice specific to your circumstances, please consult with a qualified attorney licensed in your jurisdiction.`;

    return response;
  }
}

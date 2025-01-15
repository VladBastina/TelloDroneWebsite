import { HttpClient } from '@angular/common/http';
import { AfterViewChecked, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { io, Socket } from 'socket.io-client';
import { ConnectionService } from '../connection.service';
import { timeout } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';
import { Inject, PLATFORM_ID } from '@angular/core';


@Component({
  selector: 'app-chat-page',
  imports: [CommonModule,FormsModule],
  templateUrl: './chat-page.component.html',
  styleUrl: './chat-page.component.scss'
})
export class ChatPageComponent implements OnInit, OnDestroy, AfterViewChecked {
  messages: { user: string; bot: string }[] = [];
  userMessage = '';
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

  constructor(private connectionService:ConnectionService,@Inject(PLATFORM_ID) private platformId: object) {}

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.connectionService.connect();
    } else {
      console.log('Skipping connection setup during prerendering.');
    }
  }

  sendMessage(): void {
    const userText = this.userMessage.trim();
    if (!userText) return;

    this.addUserMessage(userText);

    this.connectionService.sendMessage(userText).pipe(timeout(20000)).subscribe((response) => {
      if (!response.includes('Failed to receive a response:')) {
        this.addBotMessage(response);
      }
    });

    this.userMessage = '';
  }

  addUserMessage(userText: string): void {
    this.messages.push({ user: userText, bot: '' });
  }

  addBotMessage(botText: string): void {
    this.messages.push({ user: '', bot: botText });
  }

  ngAfterViewChecked(): void {
    if (this.messagesContainer) {
      this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
    }
  }

  ngOnDestroy(): void {
    this.connectionService.disconnect();
  }
}


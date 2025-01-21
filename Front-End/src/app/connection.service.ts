import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { Observable, Subject } from 'rxjs';
import { response } from 'express';
import { Console } from 'console';

@Injectable({
  providedIn: 'root'
})
export class ConnectionService {

  private socket!: Socket | null;
  private readonly serverUrl = 'http://localhost:5000';

  constructor() {}

  connect(): void {
    this.socket = io(this.serverUrl);

    this.socket.on('connect', () => {
      console.log('Connected to server.');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from server.');
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  cameraCon():void {
    if (this.socket != null){
    this.socket.emit('cameracon');

    this.socket.once('response',(response : any) => {console.log(response.message);})
    }
  }

  cameraDisc():void {
    if(this.socket != null){
    this.socket.emit('cameradisc');

    this.socket.once('response',(response : any) => {console.log(response.message);})
    }
  }

  sendFrame(imageData: string): Observable<string> {
    const responseSubject = new Subject<string>();

    if (this.socket) {
      this.socket.emit('frame', { data: imageData });

      this.socket.once('response', (response: any) => {
        responseSubject.next(response.message);
      });
    }

    return responseSubject.asObservable();
  }

  sendMessage(userText: string): Observable<string> {
    const responseSubject = new Subject<string>();

    if (this.socket) {
      this.socket.emit('message', { message: userText });

      this.socket.once('chatResponse', (response: any) => {
        responseSubject.next(response.message);
      });
    }

    return responseSubject.asObservable();
  }
}

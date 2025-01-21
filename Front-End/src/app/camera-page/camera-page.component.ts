import { Component, OnInit , OnDestroy, HostListener} from '@angular/core';
import { CommonModule } from '@angular/common';
import { io, Socket } from 'socket.io-client';
import { ConnectionService } from '../connection.service';

@Component({
  selector: 'app-camera-page',
  imports: [CommonModule],
  templateUrl: './camera-page.component.html',
  styleUrl: './camera-page.component.scss'
})
export class CameraPageComponent implements OnInit ,OnDestroy{
  videoElement!: HTMLVideoElement;
  canvasElement!: HTMLCanvasElement;
  items: string[] = [];
  showOverlay = false; // Overlay control
  private captureIntervalId: any;

  constructor(private connectionService: ConnectionService) {}

  ngOnInit(): void {
    this.videoElement = document.querySelector('video')!;
    this.canvasElement = document.createElement('canvas');
    this.connectionService.connect();
    this.connectionService.cameraCon();

    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        this.videoElement.srcObject = stream;
        this.videoElement.play();

        this.videoElement.onloadedmetadata = () => {
          this.videoElement.width = this.videoElement.videoWidth;
          this.videoElement.height = this.videoElement.videoHeight;
          this.startFrameCapture();
        };
      })
      .catch((err) => {
        console.error('Error accessing media devices:', err);
      });
  }

  startFrameCapture(): void {
    const context = this.canvasElement.getContext('2d')!;
    this.canvasElement.width = this.videoElement.videoWidth;
    this.canvasElement.height = this.videoElement.videoHeight;
  
    const delay = 2000;
  
    const captureAndSendFrame = () => {
      const startTime = performance.now(); // Start measuring time
  
      context.drawImage(this.videoElement, 0, 0, this.canvasElement.width, this.canvasElement.height);
      const imageData = this.canvasElement.toDataURL('image/png');
  
      if (imageData.startsWith('data:image/png')) {
        this.connectionService.sendFrame(imageData).subscribe((response) => {
          const endTime = performance.now(); // End measuring time
          const executionTime = endTime - startTime; // Calculate execution time
  
          console.log(`captureAndSendFrame execution time: ${executionTime.toFixed(2)} ms`);
  
          if (response === 'Please wait, you are not the active socket') {
            this.showOverlay = true;
          } else {
            this.showOverlay = false;
            if (
              response !== 'Already in list' &&
              !response.includes('Failed')
            ) {
              this.items.push(response);
            }
          }
          console.log('Server response:', response);
        });
      }
    };
  
    this.captureIntervalId = setInterval(captureAndSendFrame, delay);
  }

  @HostListener('window:beforeunload', ['$event'])
  handleBeforeUnload(event: Event): void {
    this.cleanupResources();
  }

  ngOnDestroy(): void {
    this.cleanupResources();
  }

  private cleanupResources(): void {

    if (this.captureIntervalId) {
      clearInterval(this.captureIntervalId);
      this.captureIntervalId = null; // Reset interval ID
    }

    this.connectionService.cameraDisc();
    this.connectionService.disconnect();

    if (this.videoElement && this.videoElement.srcObject) {
      const mediaStream = this.videoElement.srcObject as MediaStream;
      mediaStream.getTracks().forEach((track) => track.stop());
      this.videoElement.srcObject = null;
    }
  }
}

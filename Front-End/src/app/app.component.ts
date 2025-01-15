import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ConnectionService } from './connection.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  providers: [ConnectionService],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Web-Site';
}

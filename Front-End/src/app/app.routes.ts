import { RouterModule, Routes } from '@angular/router';
import { MenuComponent } from './menu/menu.component';
import { CameraPageComponent } from './camera-page/camera-page.component';
import { ChatPageComponent } from './chat-page/chat-page.component';
import { NgModule } from '@angular/core';

export const routes: Routes = [
  { path: '', redirectTo: 'menu', pathMatch: 'full' },
  { path: 'menu', component: MenuComponent },
  { path: 'camera', component: CameraPageComponent },
  { path: 'chat', component: ChatPageComponent },
  { path: '**', redirectTo: 'menu' }
];
  
  @NgModule({
    imports: [RouterModule.forRoot(routes , {useHash : false})],
    exports: [RouterModule]
  })
  export class AppRoutingModule {}
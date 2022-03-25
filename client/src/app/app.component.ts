import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { UserApiService } from './user-api.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  title = 'angular-app';
  _dropdownShown: boolean = false;

  isLoggedIn$: Observable<boolean>

  constructor(private userApi: UserApiService) {
    this.isLoggedIn$ = userApi.loginSubject;
  }


  onIconClicked(): void {
    console.log("icon clicked");
    this._dropdownShown = !this.dropdownShown;
    // this.userApi.login("taiharry108@gmail.com", "123456");
  }

  get dropdownShown(): boolean {
    return this._dropdownShown;
  }

  onLogoutClicked(): void {
    this.userApi.logout();
    this._dropdownShown = false;
  }
}

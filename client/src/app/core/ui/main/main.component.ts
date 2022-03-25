import { Component, OnDestroy, OnInit } from '@angular/core';
import { UserApiService } from 'src/app/user-api.service';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit, OnDestroy {


  constructor(private userApi: UserApiService) { }

  ngOnInit(): void {
    this.userApi.login("taiharry108@gmail.com", "123456");
  }

  ngOnDestroy(): void {
  }

}

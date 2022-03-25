import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { debounceTime, distinctUntilChanged, Subject, takeUntil } from 'rxjs';
import { UserApiService } from 'src/app/user-api.service';

@Component({
  selector: 'app-login-form',
  templateUrl: './login-form.component.html',
  styleUrls: ['./login-form.component.scss']
})
export class LoginFormComponent implements OnInit, OnDestroy {
  form: FormGroup;
  username = new FormControl('', Validators.required);
  password = new FormControl();
  ngUnsubscribe = new Subject<void>();

  constructor(private fb: FormBuilder, private userApi: UserApiService) {
    this.form = this.fb.group({
      username: this.username,
      password: this.password,
    });
  }

  ngOnInit(): void {
    this.form.valueChanges
      .pipe(takeUntil(this.ngUnsubscribe))
      .pipe(debounceTime(150), distinctUntilChanged())
      .subscribe((value) => {
        const { username, password } = value;
      });
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
  }

  onSubmit(): void {
    const { username, password } = this.form.value;
    this.userApi.login(username, password);
  }

}

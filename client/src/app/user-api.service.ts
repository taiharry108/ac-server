import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from 'src/environments/environment';
import { Manga } from './models/manga';
import { Token } from './models/token';
import { User } from './models/user';
import { Chapter } from './models/chapter';

@Injectable({
  providedIn: 'root'
})
export class UserApiService {

  userApiUrl: string = environment.userApiUrl;
  _isLoggedIn: boolean = false;
  token: string = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0YWloYXJyeTEwOEBnbWFpbC5jb20iLCJleHAiOjE2NDU1NDM3NzB9.jus9DOvzw9aGSiexycZWGnU_FRr72xUrTN2t2lcv20g";

  loginSubject = new Subject<boolean>();
  historyMangasSubject = new Subject<Manga[]>();
  historyMangas: Manga[] = [];
  latestChapSubject = new Subject<Chapter>();

  constructor(private http: HttpClient) { }

  login(username: string, password: string) {
    const url = `${this.userApiUrl}token`;

    let formData = new FormData();

    formData.append("username", username);
    formData.append("password", password);

    let lobginObserver = {
      next: (response: Token) => {
        this.token = response.access_token;
        this._isLoggedIn = true;
        this.loginSubject.next(this.isLoggedIn);
        this.getHistory();
      },
      error: (err: any) => console.error(err)
    }

    this.http.post<Token>(url, formData).subscribe(lobginObserver);
  }

  logout() {
    this._isLoggedIn = false;
    this.loginSubject.next(this.isLoggedIn);
    this.token = "";
  }

  get isLoggedIn(): boolean {
    return this._isLoggedIn;
  }

  signup(username: string, password: string) {
    const url = `${this.userApiUrl}signup`;

    let formData = new FormData();

    formData.append("username", username);
    formData.append("password", password);

    this.http.post<User>(url, formData).subscribe(
      (response) => console.log(response)
    );
  }

  readMe() {
    if (this.token === "") {
      console.error("no token");
      return;
    }
    const url = `${this.userApiUrl}me`;
    this.http.get(url, { headers: { Authorization: `Bearer ${this.token}` } }).subscribe(
      (response) => console.log(response)
    );
  }

  addHistory(mangaId: number) {
    const url = `${this.userApiUrl}add_history`;
    this.http.post(url, null,
      {
        headers: { Authorization: `Bearer ${this.token}` },
        params: new HttpParams().set("manga_id", mangaId)
      }).subscribe(
        (response) => console.log(response)
      );
  }

  getHistory() {
    const url = `${this.userApiUrl}history`;
    this.http.get<Manga[]>(url,
      {
        headers: { Authorization: `Bearer ${this.token}` },
      }).subscribe(
        (mangas) => {
          mangas.forEach((m) => {
            m.thum_img = environment.mediaServerUrl + m.thum_img;
            m.last_update = new Date(m.last_update);
          });
          this.historyMangasSubject.next(mangas);
          this.historyMangas = mangas;
        }
      );
  }

  updateLastRead(chapId: number) {
    const url = `${this.userApiUrl}update_history`;
    this.http.put(url, null,
      {
        headers: {
          Authorization: `Bearer ${this.token}`
        },
        params: new HttpParams().set("chap_id", chapId)
      }).subscribe(
        (response) => console.log(response)
      );
  }

  getLastRead(mangaId: number) {
    const url = `${this.userApiUrl}latest_chap`;
    this.http.get<Chapter>(url,
      {
        headers: {
          Authorization: `Bearer ${this.token}`
        },
        params: new HttpParams().set("manga_id", mangaId)
      }).subscribe(
        (chapter) => this.latestChapSubject.next(chapter)
      );
  }

  addFav(mangaId: number) {
    const url = `${this.userApiUrl}add_fav`;
    this.http.post(url, null,
      {
        headers: { Authorization: `Bearer ${this.token}` },
        params: new HttpParams().set("manga_id", mangaId)
      }).subscribe(
        (response) => this.getHistory()
      );
  }

  removeFav(mangaId: number) {
    const url = `${this.userApiUrl}remove_fav`;
    this.http.delete(url,
      {
        headers: { Authorization: `Bearer ${this.token}` },
        params: new HttpParams().set("manga_id", mangaId)
      }).subscribe(
        (response) => this.getHistory()
      );
  }

  isFav(mangaId: number): boolean {
    return this.historyMangas.filter((manga) => manga.id == mangaId && manga.is_fav).length == 1;
  }
}

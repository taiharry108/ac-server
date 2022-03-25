import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { MangaApiService } from 'src/app/manga-api.service';
import { Manga } from 'src/app/models/manga';
import { UserApiService } from 'src/app/user-api.service';

@Component({
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.scss']
})
export class HistoryComponent implements OnInit, OnDestroy {

  mangaList: Manga[] = [];

  counter: number = 0;

  ngUnsubscribe = new Subject<void>();

  constructor(private userApi: UserApiService,
    private cd: ChangeDetectorRef, private mangaApi: MangaApiService, private router: Router) {
  }

  ngOnInit(): void {
    this.userApi.getHistory();
    this.userApi.historyMangasSubject.pipe(takeUntil(this.ngUnsubscribe)).subscribe(mangas => {
      this.mangaList = mangas;
      this.cd.detectChanges();
    })
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
  }

  isFav(mangaId: number): boolean {
    return this.userApi.isFav(mangaId);
  }

  onfavIconClicked(mangaId: number): void {
    if (this.isFav(mangaId))
      this.userApi.removeFav(mangaId);
    else
      this.userApi.addFav(mangaId);
  }

  onCardClicked(mangaId: number): void {
    this.mangaApi.getIndexPage(mangaId);
    this.router.navigate(['/index']);
  }
}

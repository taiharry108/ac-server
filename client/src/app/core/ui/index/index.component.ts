import { Component, OnDestroy, OnInit } from '@angular/core';
import { Observable, Subject, takeUntil } from 'rxjs';
import { MangaApiService } from 'src/app/manga-api.service';
import { Chapter } from 'src/app/models/chapter';
import { Manga } from 'src/app/models/manga';
import { MangaIndexType } from 'src/app/models/manga-index-type.enum';
import { UserApiService } from 'src/app/user-api.service';

@Component({
  templateUrl: './index.component.html',
  styleUrls: ['./index.component.scss']
})
export class IndexComponent implements OnInit, OnDestroy {

  manga: Manga;
  ngUnsubscribe = new Subject<void>();

  manga$: Observable<Manga>;
  latestChap$: Observable<Chapter>;
  activatedTab: number = 0;
  MangaIndexType = MangaIndexType;
  chapIdx: number = 0;

  constructor(private mangaApi: MangaApiService, private userApi: UserApiService) {
    this.manga$ = mangaApi.mangaWithIndexSubject;
    this.latestChap$ = userApi.latestChapSubject;
    this.manga = {} as Manga;
  }


  ngOnInit(): void {
    this.manga$.pipe(takeUntil(this.ngUnsubscribe)).subscribe((manga) => {
      this.manga = manga;
      this.userApi.addHistory(manga.id);
      this.userApi.getLastRead(manga.id);
    });
  }

  onLeftDown() {
    const chapters: Chapter[] = this.manga.chapters[
      MangaIndexType[this.activatedTab]
    ];
    if (this.chapIdx > 0) this.getImages(this.chapIdx - 1);
    console.log('pressed left');
  }

  onRightDown() {
    const chapters: Chapter[] = this.manga.chapters[
      MangaIndexType[this.activatedTab]
    ];
    if (this.chapIdx < chapters.length - 1) this.getImages(this.chapIdx + 1);

    console.log('pressed right');
  }

  onFavIconClicked(mangaId: number): void {
    if (this.isFav(mangaId))
      this.userApi.removeFav(mangaId);
    else
      this.userApi.addFav(mangaId);
  }

  isFav(mangaId: number): boolean {
    return this.userApi.isFav(mangaId);
  }

  // get lastReadChapter(): Chapter {
  //   // return this.fakeItemService.genChapers(1)[0];
  //   return { title: "Test", page_url: "https://example.com", id: 1};
  // }

  get tabNames(): string[] {
    return Object.keys(this.manga.chapters);
  }

  onTabLinkClicked(idx: number) {
    this.activatedTab = idx;
  }

  private getImages(chapIdx: number) {
    console.log(chapIdx);
    const chapters: Chapter[] = this.manga.chapters[
      MangaIndexType[this.activatedTab]
    ];
    const chapter = chapters[chapIdx];
    this.mangaApi.getImages(chapter.id);
    this.userApi.updateLastRead(chapter.id);
    this.chapIdx = chapIdx;
  }

  onChapterClick(chapIdx: number) {
    this.getImages(chapIdx);
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
  }
}


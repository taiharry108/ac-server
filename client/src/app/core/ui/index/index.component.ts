import { ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
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
  viewHidden = true;

  manga$: Observable<Manga>;
  latestChap$: Observable<Chapter>;
  activatedTab: number = 0;
  MangaIndexType = MangaIndexType;
  chapIdx: number = 0;

  constructor(private mangaApi: MangaApiService, private userApi: UserApiService, private cd: ChangeDetectorRef) {
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

    if (this.chapIdx > 0) {
      this.getImages(this.chapIdx - 1);
    }
    console.log('pressed left');
  }

  onRightDown() {
    const chapters: Chapter[] = this.manga.chapters[
      MangaIndexType[this.activatedTab]
    ];

    if (this.chapIdx < chapters.length - 1) {
      this.getImages(this.chapIdx + 1);
    }

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
    console.log(this.manga);
    this.mangaApi.getImages(chapter.id);
    this.userApi.updateLastRead(chapter.id, this.manga.id);
    this.chapIdx = chapIdx;
  }

  onChapterClick(chapIdx: number) {
    this.getImages(chapIdx);
    this.viewHidden = false;
  }
  onStopClicked() {
    this.mangaApi.sseService.cancelCurrentSource();
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
  }

  onLatestChapterClick(chapterId: number): void {
    const keys = Object.keys(this.manga.chapters);
    const filteredKeys = keys.filter(key => {
      return this.manga.chapters[key].filter(chap => chap.id == chapterId).length != 0;
    })
    if (filteredKeys.length == 0) return;
    const idx = this.manga.chapters[filteredKeys[0]].findIndex(chap => chap.id == chapterId);
    this.getImages(idx);
  }

  onReverseClick(): void {
    this.manga.chapters[MangaIndexType[this.activatedTab]] = this.manga.chapters[MangaIndexType[this.activatedTab]].reverse();
  }
}


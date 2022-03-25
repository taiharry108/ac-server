import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { Observable, Subject, takeUntil } from 'rxjs';
import { MangaApiService } from 'src/app/manga-api.service';
import { Episode } from 'src/app/models/episode';
import { environment } from 'src/environments/environment';

@Component({
  templateUrl: './anime-index.component.html',
  styleUrls: ['./anime-index.component.scss']
})
export class AnimeIndexComponent implements OnInit, OnDestroy {

  ngUnsubscribe = new Subject<void>();

  episodes$: Observable<Episode[]>;

  activatedTab: number = 0;
  animeIdx: number = 0;
  vidPath: string = "";

  constructor(private mangaApi: MangaApiService, private cd: ChangeDetectorRef) {
    this.episodes$ = mangaApi.episodesSubject;
    mangaApi.episodePathSubject.pipe(takeUntil(this.ngUnsubscribe)).subscribe(
      (vidPath) => {
        this.vidPath = environment.mediaServerUrl + vidPath;
        this.cd.detectChanges();
      }
    );
  }

  ngOnInit(): void {
  }

  get anime() {
    return this.mangaApi.currentAnime;
  }

  onEpisode(episodeId: number) {
    this.mangaApi.getEpisode(episodeId);
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
  }

}

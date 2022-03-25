import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { interval, Subject, Subscription, takeUntil, timer } from 'rxjs';
import { environment } from 'src/environments/environment';
import { Anime } from './models/anime';
import { Episode } from './models/episode';
import { EpisodeResult } from './models/episodeResult';
import { Manga } from './models/manga';
import { getSiteStr, MangaSite } from './models/manga-site.enum';
import { Page } from './models/page';
import { SearchResult } from './models/search-result';
import { SseService } from './sse.service';

@Injectable({
  providedIn: 'root'
})
export class MangaApiService {

  searchResultSubject = new Subject<SearchResult[]>();
  searchAnimeResultSubject = new Subject<Anime[]>();
  mangaWithIndexSubject = new Subject<Manga>();
  episodesSubject = new Subject<Episode[]>();

  pagesSubject = new Subject<Page[]>();
  imagesSseEvent = new Subject<Page>();
  sseServiceSub: Subscription | null = null;
  unsubSSE = new Subject<void>();

  currentAnime: Anime | null = null;

  episodePathSubject = new Subject<string>();


  constructor(private http: HttpClient, private sseService: SseService) { }

  serverUrl: string = environment.serverUrl;

  private _searchEmpty = true;

  site = MangaSite.ManHuaRen;

  setSite(site: MangaSite) {
    this.site = site;
  }

  searchManga(searchKeyword: string): void {
    const siteStr = getSiteStr(this.site);
    const url = `${this.serverUrl}search/${siteStr}/${searchKeyword}`;

    this.http.get<SearchResult[]>(url).subscribe((result) => {
      this._searchEmpty = false;
      this.searchResultSubject.next(result.slice(0, 10));
    });

  }

  searchAnime(searchKeyword: string): void {
    const siteStr = getSiteStr(this.site);
    const url = `${this.serverUrl}search_anime/${siteStr}/${searchKeyword}`;

    this.http.get<Anime[]>(url).subscribe((result) => {
      this._searchEmpty = false;
      this.searchAnimeResultSubject.next(result.slice(0, 10));
    });
  }

  getIndexPage(mangaId: number): void {
    const siteStr = getSiteStr(this.site);
    const url = `${this.serverUrl}index/${siteStr}/${mangaId}`;

    this.http.get<Manga>(url, { responseType: "json" }).subscribe((result) => {
      result.thum_img = environment.mediaServerUrl + result.thum_img;
      this.mangaWithIndexSubject.next(result);
    });
  }

  setCurrentAnime(anime: Anime): void {
    this.currentAnime = anime;
  }

  getAnimeIndexPage(animeId: number): void {
    const siteStr = getSiteStr(this.site);
    const url = `${this.serverUrl}anime_index/${siteStr}/${animeId}`;

    this.http.get<Episode[]>(url, { responseType: "json" }).subscribe((result) => {
      this.episodesSubject.next(result);
    });
  }

  getImages(chapterId: number): void {
    const siteStr = getSiteStr(this.site);
    const url = `${this.serverUrl}chapter/${siteStr}/${chapterId}`;

    if (this.sseServiceSub) {
      this.sseService.cancelCurrentSource();
      this.sseServiceSub.unsubscribe();
    }

    this.sseService.startServerSentEvent(url)
    this.sseServiceSub = this.sseService.dataSubject.pipe(takeUntil(this.unsubSSE)).subscribe((page) => {
      this.imagesSseEvent.next(page);
    });
  }

  getEpisode(episodeId: number) {
    const siteStr = getSiteStr(this.site);
    const url = `${this.serverUrl}episode/${siteStr}/${episodeId}`;

    this.http.get<EpisodeResult>(url, { responseType: "json" }).subscribe((result) => {
      this.episodePathSubject.next(result["vid_path"]);
    });
  }

  emptySearch(): void {
    this._searchEmpty = true;
  }

  get searchEmpty(): boolean {
    return this._searchEmpty;
  }

}

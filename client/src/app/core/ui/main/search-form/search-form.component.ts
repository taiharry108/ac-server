import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { Observable, Subject } from 'rxjs';
import { MangaApiService } from 'src/app/manga-api.service';
import { SearchResult } from 'src/app/models/search-result';
import { takeUntil, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Router } from '@angular/router';
import { convertPySite, isMangaSite } from 'src/app/models/manga-site.enum';
import { Anime } from 'src/app/models/anime';

@Component({
  selector: 'app-search-form',
  templateUrl: './search-form.component.html',
  styleUrls: ['./search-form.component.scss']
})
export class SearchFormComponent implements OnInit, OnDestroy {
  form: FormGroup;
  search = new FormControl('', Validators.required);
  site = new FormControl();
  searchResult: Observable<SearchResult[]>;
  serachAnimeResult: Observable<Anime[]>;
  ngUnsubscribe = new Subject<void>();

  private _dropdownHidden: boolean = true;

  constructor(private fb: FormBuilder, private mangaApi: MangaApiService, private router: Router) {
    this.form = this.fb.group({
      search: this.search,
      site: this.site,
    });
    this.searchResult = this.mangaApi.searchResultSubject;
    this.serachAnimeResult = this.mangaApi.searchAnimeResultSubject;
  }

  private _search(searchKeyword: string): void {
    if (isMangaSite(this.site.value))
      this.mangaApi.searchManga(searchKeyword);
    else
      this.mangaApi.searchAnime(searchKeyword);
  }

  ngOnInit(): void {
    this.form.valueChanges
      .pipe(takeUntil(this.ngUnsubscribe))
      .pipe(debounceTime(150), distinctUntilChanged())
      .subscribe((value) => {
        const { search, site } = value;
        this.mangaApi.setSite(convertPySite(site));
        if (search.length > 3) this._search(search);
        if (search.length === 0) this.mangaApi.emptySearch();
      });
  }

  onClickOutside(): void {
    this._dropdownHidden = true;
  }

  onDivClick(): void {
    this._dropdownHidden = false;
  }

  onClick(): void {
    const { search } = this.form.value;
    this._search(search);
  }

  get dropdownHidden(): boolean {
    return this._dropdownHidden || this.mangaApi.searchEmpty;
  }

  onSuggestionClick(mangaId: number): void {
    this.mangaApi.getIndexPage(mangaId);
    this.router.navigate(['/index']);
  }

  onAnimeSuggestionClick(anime: Anime): void {
    this.mangaApi.getAnimeIndexPage(anime.id);
    this.mangaApi.setCurrentAnime(anime);
    this.router.navigate(['/anime-index']);
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
  }

}

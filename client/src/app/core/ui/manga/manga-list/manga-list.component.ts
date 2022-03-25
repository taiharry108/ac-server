import {
  ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output
} from '@angular/core';
import { Manga, MangaSimple } from 'src/app/models/manga';

@Component({
  selector: 'app-manga-list',
  templateUrl: './manga-list.component.html',
  styleUrls: ['./manga-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MangaListComponent {
  @Input() title: string = "Favorite";
  @Input() mangas: Manga[] = [];
  @Input() mediaServerUrl: string = "";

  @Output() favIconClicked = new EventEmitter<number>();
  @Output() cardClicked = new EventEmitter<number>();

  onFavIconClicked(event: Event, mangaId: number): void {
    event.stopPropagation();
    this.favIconClicked.emit(mangaId);
  }

  onCardClicked(mangaId: number) {
    this.cardClicked.emit(mangaId);
  }
}

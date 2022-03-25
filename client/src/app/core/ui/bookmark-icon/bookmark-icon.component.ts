import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-bookmark-icon',
  templateUrl: './bookmark-icon.component.html',
  styleUrls: ['./bookmark-icon.component.scss']
})
export class BookmarkIconComponent {
  @Input() isFav: boolean = false;
  @Input() size: number = 2;
}

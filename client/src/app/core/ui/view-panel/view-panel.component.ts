import { ChangeDetectorRef, Component, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { Subject, takeUntil } from 'rxjs';
import { MangaApiService } from 'src/app/manga-api.service';
import { environment } from 'src/environments/environment';
import { FakeItemService } from '../../fake-item.service';

@Component({
  selector: 'app-view-panel',
  templateUrl: './view-panel.component.html',
  styleUrls: ['./view-panel.component.scss']
})
export class ViewPanelComponent implements OnInit, OnDestroy {
  pages: SafeUrl[] = [];
  ngUnsubscribe = new Subject<void>();
  @Output() clickLeft = new EventEmitter<void>();
  @Output() clickRight = new EventEmitter<void>();

  constructor(private mangaApi: MangaApiService, private fakeItemService: FakeItemService, private cd: ChangeDetectorRef, private sanitizer: DomSanitizer,) {

  }

  ngOnInit(): void {
    this.mangaApi.imagesSseEvent
      .pipe(takeUntil(this.ngUnsubscribe))
      .subscribe((page) => {
        const total = page.total;
        if (
          this.pages === null ||
          this.pages.length !== total ||
          this.pages[page.idx] !== undefined
        ) {
          this.pages = new Array(total);
        }
        this.pages[page.idx] = this.sanitizer.bypassSecurityTrustUrl(
          environment.mediaServerUrl + page.pic_path
        );

        this.cd.detectChanges();
      });
    this.mangaApi.pagesSubject.pipe(takeUntil(this.ngUnsubscribe)).subscribe((pages) => {
      this.pages = pages.map((page) => {
        return page;
      });
    });
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
    this.ngUnsubscribe.complete();
  }

  onImageContainerClick(event: MouseEvent): void {
    const imageCtnr = document.getElementById('image-container');
    const width = imageCtnr?.clientWidth;
    if (width) {
      const half = width / 2;
      if (event.offsetX > half)
        this.clickRight.emit();
      else
        this.clickLeft.emit();
    }
    

    
    console.log(`offsetX,Y=(${event.offsetX}, ${event.offsetY})`);
  }
}

import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
  selector: 'app-tabs',
  templateUrl: './tabs.component.html',
  styleUrls: ['./tabs.component.scss']
})
export class TabsComponent implements OnInit {

  @Input() tabNames: string[] =[];
  @Input() maxWidth: number = 100;
  @Output() tabActivateEvent = new EventEmitter<number>();

  activatedTab: number = 0;

  constructor() { }

  ngOnInit(): void {
  }

  onTabLinkClicked(idx: number) {
    this.activatedTab = idx;
    this.tabActivateEvent.emit(idx);
  }

  get maxWidthClass(): string {
    return `max-w-[${this.maxWidth}%]`;
  }

}

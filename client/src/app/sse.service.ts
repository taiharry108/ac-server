import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { Page } from './models/page';

@Injectable({
  providedIn: 'root'
})
export class SseService {
  dataSubject = new Subject<any>();

  private cancelledSet = new Set();
  private currentUrl = "";

  public cancelCurrentSource(): void {
    this.cancelledSet.add(this.currentUrl);
  }

  startServerSentEvent(url: string): void {
    this.currentUrl = url;
    const eventSource = this.getEventSource(url);
    eventSource.onmessage = event => {
      const data = JSON.parse(event.data);
      console.log(this.cancelledSet);
      if (this.cancelledSet.has(eventSource.url)) {
        eventSource.close();
        this.cancelledSet.delete(eventSource.url);
      }

      console.log(eventSource.url);
      if (event.data !== "{}")
        this.dataSubject.next(data);
      else
        eventSource.close();
    }

    eventSource.onerror = error => {
      console.log(error);
      this.dataSubject.error(error);
    }
  }

  private getEventSource(url: string): EventSource {
    return new EventSource(url);
  }
}

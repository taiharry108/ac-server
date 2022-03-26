import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { Page } from './models/page';

@Injectable({
  providedIn: 'root'
})
export class SseService {
  dataSubject = new Subject<any>();

  private currentSource: EventSource | null = null;

  public cancelCurrentSource(): void {
    this.currentSource?.close();
    this.currentSource = null;
  }

  startServerSentEvent(url: string): void {
    this.currentSource = this.getEventSource(url);
    this.currentSource.onmessage = event => {
      const data = JSON.parse(event.data);      
      if (event.data !== "{}")
        this.dataSubject.next(data);
      else {
        this.currentSource?.close();
        this.currentSource = null;
      }
    }

    this.currentSource.onerror = error => {
      console.log(error);
      this.dataSubject.error(error);
    }
  }

  private getEventSource(url: string): EventSource {
    return new EventSource(url);
  }
}

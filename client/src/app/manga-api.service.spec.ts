import { TestBed } from '@angular/core/testing';

import { MangaApiService } from './manga-api.service';

describe('MangaApiService', () => {
  let service: MangaApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MangaApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

import { TestBed } from '@angular/core/testing';

import { FakeItemService } from './fake-item.service';

describe('FakeItemService', () => {
  let service: FakeItemService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FakeItemService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnimeIndexComponent } from './anime-index.component';

describe('AnimeIndexComponent', () => {
  let component: AnimeIndexComponent;
  let fixture: ComponentFixture<AnimeIndexComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AnimeIndexComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AnimeIndexComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

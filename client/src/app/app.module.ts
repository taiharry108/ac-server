import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { MainComponent } from './core/ui/main/main.component';
import { SearchFormComponent } from './core/ui/main/search-form/search-form.component';
import { MangaListComponent } from './core/ui/manga/manga-list/manga-list.component';

import { MangaSitePipe } from './models/manga-site.pipe';
import { HistoryComponent } from './core/ui/manga/history/history.component';
import { IndexComponent } from './core/ui/index/index.component';
import { BookmarkIconComponent } from './core/ui/bookmark-icon/bookmark-icon.component';
import { TabsComponent } from './core/ui/common/tabs/tabs.component';
import { ClickOutsideDirective } from './core/ui/click-outside.directive';
import { ViewPanelComponent } from './core/ui/view-panel/view-panel.component';
import { LoginButtonComponent } from './core/ui/login-button/login-button.component';
import { LoginFormComponent } from './core/ui/login-form/login-form.component';
import { FavoriteComponent } from './core/ui/manga/favorite/favorite.component';
import { AnimeIndexComponent } from './core/ui/anime-index/anime-index.component';

@NgModule({
  declarations: [
    AppComponent,
    MainComponent,
    SearchFormComponent,
    MangaListComponent,
    MangaSitePipe,
    HistoryComponent,
    IndexComponent,
    BookmarkIconComponent,
    TabsComponent,
    ClickOutsideDirective,
    ViewPanelComponent,
    LoginButtonComponent,
    LoginFormComponent,
    FavoriteComponent,
    AnimeIndexComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    ReactiveFormsModule,
    HttpClientModule,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }

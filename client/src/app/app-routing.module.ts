import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AnimeIndexComponent } from './core/ui/anime-index/anime-index.component';
import { IndexComponent } from './core/ui/index/index.component';
import { MainComponent } from './core/ui/main/main.component';
import { FavoriteComponent } from './core/ui/manga/favorite/favorite.component';
import { HistoryComponent } from './core/ui/manga/history/history.component';

const routes: Routes = [
  { path: '', component: MainComponent },
  { path: 'history', component: HistoryComponent },
  { path: 'favorite', component: FavoriteComponent },
  { path: 'index', component: IndexComponent },
  { path: 'anime-index', component: AnimeIndexComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

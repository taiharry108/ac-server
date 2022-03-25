import { Chapter } from './chapter';

export interface IMap<T> {
  [index: string]: T;
}

export interface Manga {
    id: number;
    name: string;
    url: string;
    chapters: IMap<Chapter[]>;
    finished: boolean;
    thum_img: string;
    last_update: string | Date;
    site: string;
    latest_chapter?: Chapter;
    is_fav: boolean;
}

export interface MangaSimple {
    id: number;
    isFav: boolean;
}

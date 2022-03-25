import { Injectable } from '@angular/core';
import { Chapter } from '../models/chapter';
import { Manga, IMap } from '../models/manga';
import { Page } from '../models/page';

@Injectable({
  providedIn: 'root'
})
export class FakeItemService {

  constructor() { }

  private createManga(id: number): Manga {
    return {
      id: id,
      name: "火影忍者",
      url: "test",
      chapters: {
        Chapters: [{ title: "第710话", page_url: "https://www.manhuaren.com/m208255/", id: 521}]
      },
      finished: true,
      thum_img: "http://localhost:8001/thum_img/a0805d81f44ff0b7c496708388817a18.jpeg",
      last_update: "last update str",
      site: "site",
      // latest_chapters?: Map<string, Chapter>,
      is_fav: true
    }
  }

  private createChapter(id: number): Chapter {
    return {
      title: `test chapter title ${id}`,
      page_url: `test page url ${id}`,
      id: id
    }
  }

  public genChapers(n: number): Chapter[] {
    let chapterList: Chapter[] = [];
    for (let index = 0; index < n; index++) {
      let chapter: Chapter = this.createChapter(index);
      chapterList.push(chapter);
    }
    return chapterList;
  }

  public genMangas(n: number): Manga[] {
    let mangaList: Manga[] = [];
    for (let index = 0; index < n; index++) {
      let manga: Manga = this.createManga(index);

      // manga.chapters = new Map();
      // manga.chapters.set("Type 1", chapters);
      // manga.chapters.set("Type 2", this.genChapers(5));

      mangaList.push(manga);

    }
    return mangaList;
  }

  public getPages(): Page[] {
    // return [{ "pic_path": "manhuaren/火影忍者/第710话/c638ea38cc79438ec340c0229403b6fe.png", "idx": 0 }, { "pic_path": "manhuaren/火影忍者/第710话/5e72c4ace4485906dc0408f95d8f5027.png", "idx": 1 }, { "pic_path": "manhuaren/火影忍者/第710话/34824981cc2f720d1f331bc1c3773bd2.png", "idx": 2 }, { "pic_path": "manhuaren/火影忍者/第710话/11cfe789195b9e5a8ea87882a7d5ad2e.png", "idx": 3 }, { "pic_path": "manhuaren/火影忍者/第710话/f6e0e35a24309cd4dd4e86c253528fde.png", "idx": 4 }, { "pic_path": "manhuaren/火影忍者/第710话/f141ef36dd91b9985288d3662d3e0994.png", "idx": 5 }, { "pic_path": "manhuaren/火影忍者/第710话/de174e83ca84751721ed1c8725dbe276.png", "idx": 6 }, { "pic_path": "manhuaren/火影忍者/第710话/c8aa3dbe769e0c34e7ec46ccfde82270.png", "idx": 7 }, { "pic_path": "manhuaren/火影忍者/第710话/1470652f67bf92dace6183524d933c15.png", "idx": 8 }, { "pic_path": "manhuaren/火影忍者/第710话/8d8e413091a8263d488a958eb6a29b5f.png", "idx": 9 }, { "pic_path": "manhuaren/火影忍者/第710话/a82776f29896c230ee7c53fb328f2cb1.png", "idx": 10 }, { "pic_path": "manhuaren/火影忍者/第710话/f2b3df2504ea0dd28f1da46d59e61b27.png", "idx": 11 }, { "pic_path": "manhuaren/火影忍者/第710话/0d39eea8ec4a1c933270562f7424ae7d.png", "idx": 12 }, { "pic_path": "manhuaren/火影忍者/第710话/f6362f9e5948fc1bde2efc2cb322dfd0.png", "idx": 13 }, { "pic_path": "manhuaren/火影忍者/第710话/041d9c21c88a3b8b627e7b18cac444e8.png", "idx": 14 }, { "pic_path": "manhuaren/火影忍者/第710话/1dbdcc96e43eb7a70a1efdc4b6e977d1.png", "idx": 15 }, { "pic_path": "manhuaren/火影忍者/第710话/1901db8f1a84835a9c906d96b8ea5e96.png", "idx": 16 }, { "pic_path": "manhuaren/火影忍者/第710话/b147644b467062216a79c9e4855f4c03.png", "idx": 17 }, { "pic_path": "manhuaren/火影忍者/第710话/6a8db55b5b0ae7066fda21fe4e37f1fa.jpeg", "idx": 18 }];
    return [];
  }
}

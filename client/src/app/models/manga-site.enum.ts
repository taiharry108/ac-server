export enum MangaSite {
  ManHuaRen = '漫畫人',
  Anime1 = 'Anime1',
}

export const getAllSites = () => {
  return [MangaSite.ManHuaRen, MangaSite.Anime1];
}

export const isMangaSite = (siteStr: string): boolean => {
  const site = convertPySite(siteStr);
  switch (site) {
    case MangaSite.ManHuaRen:
      return true;
    case MangaSite.Anime1:
      return false;
    default:
      return true;
  }
}

export const getSiteStr = (site: MangaSite): string => {
  switch (site) {
    case MangaSite.ManHuaRen:
      return 'manhuaren';
    case MangaSite.Anime1:
      return 'anime1';
    default:
      return 'manhuaren';
  }
}

export const convertPySite = (value: string): MangaSite => {
  let site: MangaSite = MangaSite.ManHuaRen;
  switch (value) {
    case 'manhuaren': {
      site = MangaSite.ManHuaRen;
      break;
    }
    case 'anime1': {
      site = MangaSite.Anime1;
      break;
    }
  }
  return site;
};

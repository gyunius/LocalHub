export interface TourItem {
  contentid: string;
  contenttypeid: string;
  title: string;
  addr1: string;
  addr2?: string;
  zipcode?: string;
  tel?: string;
  mapx?: string; // 원본은 string — 필요시 parseFloat 사용
  mapy?: string;
  mlevel?: string;
  areacode?: string;
  sigungucode?: string;
  lDongRegnCd?: string;
  lDongSignguCd?: string;
  cat1?: string;
  cat2?: string;
  cat3?: string;
  lclsSystm1?: string;
  lclsSystm2?: string;
  lclsSystm3?: string;
  firstimage?: string;
  firstimage2?: string;
  cpyrhtDivCd?: string;
  createdtime?: string;
  modifiedtime?: string;

  // 추가: 런타임에서 범위 밖/오류 항목을 비활성화 표시
  disabled?: boolean;
}

export interface TourApiResponse {
  region: string;
  contentType: string;
  contentTypeId: string;
  total: number;
  items: TourItem[];
}
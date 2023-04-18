export interface Page {
    id: number;
    meta: PageMeta;
    title: string;
    [key: string]: any;
}

interface PageMeta {
    type: string;
    [key: string]: any;
}

export interface ImageInfo {
    id: number;
}

export interface Image {
    rendition: ImageRendition;
}

export interface ImageRendition {
    url: string;
    alt: string;
    width: number;
    height: number;
}

export interface Block {
    id: string;
    type: string;
    value: any;
}

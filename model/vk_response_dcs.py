from __future__ import annotations  # Postponed annotation calculation
from dataclasses import dataclass

@dataclass(frozen=True)
class Updates:
    ts: str
    updates: list[UpdateUnit]

    @classmethod
    def from_raw_data(cls, data: dict) -> Updates:
        updates = data.get('updates', None)
        return cls(
            ts=data['ts'],
            updates=[UpdateUnit.from_raw_data(update) for update in updates]
        )


@dataclass(frozen=True)
class UpdateUnit:
    group_id: int
    type: str
    event_id: str
    v: str
    object: UpdatePayload

    @classmethod
    def from_raw_data(cls, data: dict) -> UpdateUnit:
        object = data.get('object', None)
        return cls(
            group_id=data['group_id'],
            type=data['type'],
            event_id=data['event_id'],
            v=data['v'],
            object=UpdatePayload.from_raw_data(object) if object else None
        )


@dataclass(frozen=True)
class UpdatePayload:
    inner_type: str
    can_edit: int
    created_by: int
    can_delete: int
    donut: dict  # В рамках данного проекта не требует дальнейшей детализации
    comments: dict  # В рамках данного проекта не требует дальнейшей детализации
    marked_as_ads: int
    hash: str
    type: str
    post_author_data: dict  # В рамках данного проекта не требует дальнейшей детализации
    date: int
    from_id: int
    header: dict  # В рамках данного проекта не требует дальнейшей детализации
    id: int
    is_favorite: bool
    reaction_set_id: str
    badges: dict  # В рамках данного проекта не требует дальнейшей детализации
    owner_id: int
    post_type: str
    text: str
    attachments: list[Attachment]
    zoom_text: bool = None
    attachments_meta: dict | None = None  # В рамках данного проекта не требует дальнейшей детализации

    @classmethod
    def from_raw_data(cls, data: dict) -> UpdatePayload:
        attachments_data = data.get('attachments', [])
        return cls(
            inner_type=data['inner_type'],
            can_edit=data['can_edit'],
            created_by=data['created_by'],
            can_delete=data['can_delete'],
            donut=data.get('donut', {}),
            comments=data.get('comments', {}),
            marked_as_ads=data.get('marked_as_ads', 0),
            zoom_text=data.get('zoom_text', False),
            hash=data.get('hash', ''),
            type=data['type'],
            post_author_data=data.get('post_author_data', {}),
            date=data['date'],
            from_id=data['from_id'],
            header=data.get('header', {}),
            id=data['id'],
            is_favorite=data.get('is_favorite', False),
            reaction_set_id=data.get('reaction_set_id', ''),
            badges=data.get('badges', {}),
            owner_id=data['owner_id'],
            post_type=data['post_type'],
            text=data['text'],
            attachments=[Attachment.from_raw_data(a) for a in attachments_data],
            attachments_meta=data.get('attachments_meta'),
        )


@dataclass(frozen=True)
class Attachment:
    type: str
    photo: Photo
    style: str

    @classmethod
    def from_raw_data(cls, data: dict) -> Attachment:
        photo = data.get('photo', None)
        return cls(
            type=data['type'],
            photo=Photo.from_raw_data(photo) if photo else None,
            style=data['style']
        )


@dataclass(frozen=True)
class Photo:
    album_id: int
    date: int
    id: int
    owner_id: int
    access_key: str
    crop_data: list
    sizes: list
    text: str
    user_id: int
    web_view_token: str
    has_tags: bool
    orig_photo: OrigPhoto
    photo_before_crop: dict = None  # В рамках данного проекта не требует дальнейшей детализации
    post_id: int = None

    @classmethod
    def from_raw_data(cls, data: dict) -> Photo:
        orig_photo = data.get('orig_photo', None)
        return cls(
            album_id=data['album_id'],
            date=data['date'],
            id=data['id'],
            owner_id=data['owner_id'],
            access_key=data['access_key'],
            crop_data=data.get('crop_data', None),
            sizes=data['sizes'],
            text=data['text'],
            user_id=data['user_id'],
            web_view_token=data['web_view_token'],
            has_tags=data['has_tags'],
            photo_before_crop=data.get('photo_before_crop', None),  # В рамках данного проекта не требует дальнейшей детализации
            post_id=data.get('post_id', None),
            orig_photo=OrigPhoto.from_raw_data(orig_photo) if orig_photo else None
        )


@dataclass(frozen=True)
class OrigPhoto:
    height: int
    type: str
    url: str
    width: int

    @classmethod
    def from_raw_data(cls, data: dict) -> OrigPhoto:
        return cls(
            height=data['height'],
            type=data['type'],
            url=data['url'],
            width=data['width']
        )
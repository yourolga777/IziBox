export type ContactTypeValue = 'personal' | 'needed' | 'spam' | 'other'

export interface Contact {
  id: number
  name: string | null
  phone: string | null
  email: string | null
  telegram_id: string | null
  telegram_username: string | null
  is_known: boolean
  is_favorite: boolean
  is_blocked?: boolean
  contact_type: ContactTypeValue
  birthday?: string | null
  notes: string | null
  channel_types: string[]
  folder_id: number | null
  last_message_at: string | null
  deleted_at: string | null
  created_at: string | null
  updated_at: string | null
  message_count?: number
  task_count?: number
}

export type ContactSortBy = 'name' | 'created_at' | 'message_count' | 'last_activity' | 'first_message' | 'has_tasks'
export type ContactSubsection = 'new'

export interface ContactsQueryParams {
  search?: string
  channel?: string
  subsection?: ContactSubsection
  contact_type?: ContactTypeValue
  folder_id?: number
  is_favorite?: boolean
  sort_by?: ContactSortBy
  sort_order?: 'asc' | 'desc'
  skip?: number
  limit?: number
}

export interface ContactCreate {
  name?: string | null
  phone?: string | null
  email?: string | null
  telegram_id?: string | null
  telegram_username?: string | null
  notes?: string | null
  contact_type?: ContactTypeValue | null
  birthday?: string | null
  is_known?: boolean | null
  is_favorite?: boolean | null
  folder_id?: number | null
}

export interface ContactUpdate {
  name?: string | null
  phone?: string | null
  email?: string | null
  telegram_id?: string | null
  telegram_username?: string | null
  is_known?: boolean | null
  is_favorite?: boolean | null
  contact_type?: ContactTypeValue | null
  birthday?: string | null
  folder_id?: number | null
  notes?: string | null
}

export interface ContactFolder {
  id: number
  name: string
  color: string | null
  sort_order: number
  is_default: boolean
  category_key: string | null
  contact_type: string | null
  parent_id: number | null
  created_at: string | null
  updated_at?: string | null
}

export interface ContactFolderCreate {
  name: string
  color?: string | null
  sort_order?: number
  category_key?: string | null
  contact_type?: string | null
  parent_id?: number | null
}

export interface ContactFolderUpdate {
  name?: string
  color?: string | null
  sort_order?: number
  category_key?: string | null
  contact_type?: string | null
  parent_id?: number | null
}

export interface BulkUpdateRequest {
  ids: number[]
  is_known?: boolean | null
  folder_id?: number | null
  is_favorite?: boolean | null
  contact_type?: ContactTypeValue | null
}

export interface DuplicateGroup {
  contacts: Contact[]
  reason: string
}

export interface TimelineEvent {
  type: string
  title: string
  subtitle: string
  created_at: string | null
  link: string | null
}

export interface ContactNote {
  id: number
  content: string
  author: string | null
  created_at: string | null
}

export interface ContactNoteCreate {
  content: string
  author?: string | null
}

export interface ImportResult {
  created: number
  updated: number
}

export interface DashboardChannelStats {
  channel: string
  count: number
}

export interface DashboardContactStats {
  contact_id: number
  contact_name: string | null
  message_count: number
}

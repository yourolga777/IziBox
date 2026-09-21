import type { ChatFilters, ChatItem } from '../types/inbox'

export function filterChats(chats: ChatItem[], filters: ChatFilters): ChatItem[] {
  let result = chats

  if (filters.contactType === 'spam') {
    result = result.filter((c) => c.contact.contact_type === 'spam')
  } else if (filters.contactType) {
    result = result.filter(
      (c) => c.contact.contact_type !== 'spam' && c.contact.contact_type === filters.contactType,
    )
  } else {
    result = result.filter((c) => c.contact.contact_type !== 'spam')
  }

  if (filters.channel) {
    result = result.filter((c) => c.channels.has(filters.channel!))
  }

  if (filters.showOnlyNew) {
    result = result.filter((c) => c.unreadCount > 0)
  }

  if (filters.folder === 'other') {
    result = result.filter((c) => c.contact.contact_type === 'other')
  } else if (filters.folder != null) {
    result = result.filter((c) => c.contact.folder_id === filters.folder)
  }

  if (filters.favorites) {
    result = result.filter((c) => c.contact.is_favorite)
  }

  if (filters.searchQuery) {
    const q = filters.searchQuery.toLowerCase()
    result = result.filter((c) => {
      const nameMatch = (c.contact.name || '').toLowerCase().includes(q)
      const msgMatch = c.lastMessage.content.toLowerCase().includes(q)
      return nameMatch || msgMatch
    })
  }

  return result
}

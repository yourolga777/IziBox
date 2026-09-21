import type { ContactTypeValue } from './contact'

export const CONTACT_TYPES: ContactTypeValue[] = [
  'personal',
  'needed',
  'spam',
  'other',
]

export const CONTACT_TYPE_META: Record<ContactTypeValue, { label: string; color: string; bg: string }> = {
  personal: { label: 'Личное', color: 'text-green-700', bg: 'bg-green-100' },
  needed: { label: 'Нужное', color: 'text-blue-700', bg: 'bg-blue-100' },
  spam: { label: 'Спам', color: 'text-gray-600', bg: 'bg-gray-100' },
  other: { label: 'Другое', color: 'text-gray-500', bg: 'bg-gray-50' },
}

export const CONTACT_TYPE_FILTERS: { key: ContactTypeValue | ''; label: string }[] = [
  { key: '', label: 'Все типы' },
  ...CONTACT_TYPES.map((t) => ({ key: t, label: CONTACT_TYPE_META[t].label })),
]

export function contactTypeLabel(value: string | null | undefined): string {
  if (value && value in CONTACT_TYPE_META) return CONTACT_TYPE_META[value as ContactTypeValue].label
  return 'Другое'
}

export function contactTypeMeta(value: string | null | undefined): { label: string; color: string; bg: string } {
  if (value && value in CONTACT_TYPE_META) return CONTACT_TYPE_META[value as ContactTypeValue]
  return CONTACT_TYPE_META.other
}

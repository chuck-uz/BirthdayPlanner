export type TelegramDelivery = {
  can_receive_bot_messages: boolean
  bot_username: string | null
}

export type SubscriptionState = {
  subscribed: boolean
  can_receive_bot_messages: boolean
  bot_username: string | null
}

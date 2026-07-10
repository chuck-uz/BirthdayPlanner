export type GroupSubscriptionState = {
  subscribed: boolean
  /** Есть ли сейчас хотя бы одна общая группа с этим человеком. */
  can_subscribe: boolean
}

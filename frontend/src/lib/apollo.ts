import { ApolloClient, InMemoryCache, HttpLink, from } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'

const STORAGE_KEY = 'reshith_auth'

const graphqlUri = import.meta.env.VITE_GRAPHQL_URL || '/graphql'

const httpLink = new HttpLink({ uri: graphqlUri })

const authLink = setContext((_, { headers }) => {
  let token: string | null = null
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) token = JSON.parse(raw).token ?? null
  } catch {
    token = null
  }
  return {
    headers: {
      ...(headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  }
})

export const client = new ApolloClient({
  link: from([authLink, httpLink]),
  cache: new InMemoryCache(),
})

import { ApolloClient, HttpLink, InMemoryCache } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'

const STORAGE_KEY = 'reshith_auth'

const graphqlUri = import.meta.env.VITE_GRAPHQL_URL || '/graphql'

const httpLink = new HttpLink({ uri: graphqlUri })

const authLink = setContext((_operation, { headers }) => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const { token } = JSON.parse(raw) as { token?: string }
      if (token) {
        return { headers: { ...headers, Authorization: `Bearer ${token}` } }
      }
    }
  } catch {
    // localStorage unavailable or JSON malformed — fall through to no auth.
  }
  return { headers }
})

export const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
})

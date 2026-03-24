import { ApolloClient, InMemoryCache } from '@apollo/client'

const graphqlUri = import.meta.env.VITE_GRAPHQL_URL || '/graphql'

export const client = new ApolloClient({
  uri: graphqlUri,
  cache: new InMemoryCache(),
})

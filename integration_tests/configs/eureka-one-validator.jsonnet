local default = import 'default.jsonnet';

default {
  'cronos_777-1'+: {
    // Override to use only one validator instead of three
    validators: [{
      coins: '1000000000000000000stake,10000000000000000000000basetcro',
      staked: '1000000000000000000stake',
      mnemonic: '${VALIDATOR1_MNEMONIC}',
      client_config: {
        'broadcast-mode': 'sync',
      },
      'app-config': {
        memiavl: {
          enable: true,
          'zero-copy': true,
          'snapshot-interval': 5,
          'cache-size': 0,
          'async-commit-buffer': 5,
        },
        versiondb: {
          enable: true,
        },
        evm: {
          'block-executor': 'block-stm',
          'block-stm-workers': 32,
        },
      },
    }],
    // Keep the accounts from default config (community, signer1, signer2)
    accounts: default['cronos_777-1'].accounts,
    config+: {
      tx_index+: {
        // Enable transaction indexing for governance proposal queries
        indexer: 'kv',
      },
    },
    'app-config'+: {
      'json-rpc'+: {
        'enable-indexer': true,
      },
    },
    genesis+: {
      app_state+: {
        feemarket+: {
          params+: {
            min_gas_multiplier: '0',
          },
        },
      },
    },
  },
}


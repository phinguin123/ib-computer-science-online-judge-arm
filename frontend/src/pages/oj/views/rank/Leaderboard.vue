<template>
  <Row type="flex" justify="space-around">
    <Col :span="22">
    <Panel :padding="10" class="leaderboard-panel">
      <div slot="title">Leaderboard</div>
      <Table :data="leaderboardData" :columns="columns" :loading="loadingTable" size="large" class="leaderboard-table"></Table>
      <Pagination :total="total" :page-size.sync="limit" :current.sync="page"
                  @on-change="getLeaderboardData" show-sizer
                  @on-page-size-change="getLeaderboardData(1)"></Pagination>
    </Panel>
    </Col>
  </Row>
</template>

<script>
  import api from '@oj/api'
  import Pagination from '@oj/components/Pagination'

  export default {
    name: 'leaderboard',
    components: {
      Pagination
    },
    data () {
      return {
        page: 1,
        limit: 30,
        total: 0,
        loadingTable: false,
        leaderboardData: [],
        allData: [],
        columns: [
          {
            title: 'Rank #',
            align: 'center',
            width: 80,
            render: (h, params) => {
              return h('span', {}, params.index + (this.page - 1) * this.limit + 1)
            }
          },
          {
            title: 'User',
            align: 'left',
            render: (h, params) => {
              return h('div', {
                style: {
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-start'
                }
              }, [
                h('img', {
                  style: {
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    marginRight: '10px',
                    flexShrink: 0,
                    objectFit: 'cover'
                  },
                  attrs: {
                    src: params.row.avatar || '/public/avatar/default.png'
                  },
                  on: {
                    error: (e) => {
                      // Prevent infinite loop - only set default if not already trying to load it
                      if (e.target.src && !e.target.src.includes('default.png')) {
                        e.target.src = '/public/avatar/default.png'
                      } else {
                        // If default.png also fails, use a data URI placeholder to stop the loop
                        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiNEOUQ5RDkiLz4KPHBhdGggZD0iTTE2IDEwQzE4LjIwOTEgMTAgMjAgMTEuNzkwOSAyMCAxNEMyMCAxNi4yMDkxIDE4LjIwOTEgMTggMTYgMThDMTMuNzkwOSAxOCAxMiAxNi4yMDkxIDEyIDE0QzEyIDExLjc5MDkgMTMuNzkwOSAxMCAxNiAxMFoiIGZpbGw9IiM5OTk5OTkiLz4KPHBhdGggZD0iTTE2IDIyQzE4LjY2NjcgMjIgMjEgMjAuNjY2NyAyMSAxOEgyMUMxOSAyMi4yMDkxIDE3LjIwOTEgMjQgMTUgMjRIMTdDMTQuMzMzMyAyNCAxMiAyMi42NjY3IDEyIDIwSDEyQzEyIDIyLjIwOTEgMTMuNzkwOSAyNCAxNiAyNFoiIGZpbGw9IiM5OTk5OTkiLz4KPC9zdmc+'
                        e.target.onerror = null // Remove error handler to prevent further loops
                      }
                    }
                  }
                }),
                h('a', {
                  style: {
                    display: 'inline-block',
                    maxWidth: '200px',
                    verticalAlign: 'middle',
                    lineHeight: '32px'
                  },
                  on: {
                    click: () => {
                      this.$router.push({
                        name: 'user-home',
                        query: {username: params.row.username}
                      })
                    }
                  }
                }, params.row.username)
              ])
            }
          },
          {
            title: 'Tier',
            align: 'center',
            render: (h, params) => {
              const tier = params.row.tier
              const tierClass = this.getTierClass(tier)
              return h('span', {
                class: tierClass
              }, tier)
            }
          },
          {
            title: 'AC / Total',
            align: 'center',
            render: (h, params) => {
              return h('span', {}, `${params.row.accepted_number} / ${params.row.submission_number}`)
            }
          },
          {
            title: 'Score',
            align: 'center',
            key: 'total_score'
          }
        ]
      }
    },
    mounted () {
      this.getLeaderboardData(1)
    },
    methods: {
      getLeaderboardData (page) {
        this.page = page || this.page
        // Fetch all data once, then paginate client-side
        if (this.allData.length === 0) {
          this.loadingTable = true
          api.getLeaderboard(0, 100).then(res => {
            this.allData = res.data.data
            this.total = this.allData.length
            this.updatePageData()
            this.loadingTable = false
          }).catch(() => {
            this.loadingTable = false
          })
        } else {
          // Client-side pagination is instant, no loading needed
          this.updatePageData()
        }
      },
      updatePageData () {
        let offset = (this.page - 1) * this.limit
        this.leaderboardData = this.allData.slice(offset, offset + this.limit)
      },
      getTierClass (tier) {
        if (!tier) return ''
        const tierLower = tier.toLowerCase()
        if (tierLower.includes('master')) {
          return 'tier-master'
        } else if (tierLower.includes('diamond')) {
          return 'tier-diamond'
        } else if (tierLower.includes('platinum')) {
          return 'tier-platinum'
        } else if (tierLower.includes('gold')) {
          return 'tier-gold'
        } else if (tierLower.includes('silver')) {
          return 'tier-silver'
        } else if (tierLower.includes('bronze')) {
          return 'tier-bronze'
        }
        return ''
      }
    }
  }
</script>

<style lang="less">
  @keyframes shimmer {
    0% {
      background-position: 0% 50%;
    }
    100% {
      background-position: 200% 50%;
    }
  }

  /* Global styles for tier colors - needed because iView Table render functions create elements outside scoped scope */
  .leaderboard-panel {
    .tier-master {
      background: linear-gradient(90deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3, #ff0000);
      background-size: 200% 100%;
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      text-fill-color: transparent;
      font-weight: bold;
      animation: shimmer 3s linear infinite;
      display: inline-block;
    }

    .tier-diamond {
      color: #00d4ff !important;
      font-weight: bold;
    }

    .tier-platinum {
      color: #00b8a9 !important;
      font-weight: bold;
    }

    .tier-gold {
      color: #ffa500 !important;
      font-weight: bold;
    }

    .tier-silver {
      color: #c0c0c0 !important;
      font-weight: bold;
    }

    .tier-bronze {
      color: #cd7f32 !important;
      font-weight: bold;
    }
  }
</style>


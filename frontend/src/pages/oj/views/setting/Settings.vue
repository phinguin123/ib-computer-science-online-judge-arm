<template>
  <div class="container">
    <Card :padding="0">
      <div class="flex-container">
        <div class="menu">
          <Menu accordion @on-select="goRoute" :activeName="activeName" style="text-align: center;" width="auto">
            <div class="avatar-editor">
              <div class="avatar-container">
                <img class="avatar" :src="profile.avatar || '/public/avatar/default.png'" @error="handleAvatarError"/>
                <div class="avatar-mask">
                  <a @click.stop="goRoute({name: 'profile-setting'})">
                    <div class="mask-content">
                      <Icon type="camera" size="30"></Icon>
                      <p class="text">change avatar</p>
                    </div>
                  </a>
                </div>
              </div>
            </div>

            <Menu-item name="/setting/profile">{{$t('m.Profile')}}</Menu-item>
            <Menu-item name="/setting/account">{{$t('m.Account')}}</Menu-item>
            <Menu-item name="/setting/security">{{$t('m.Security')}}</Menu-item>
          </Menu>
        </div>
        <div class="panel">
          <transition name="fadeInUp">
            <router-view></router-view>
          </transition>
        </div>
      </div>
    </Card>
  </div>
</template>
<script>
  import { mapGetters } from 'vuex'

  export default {
    name: 'profile',
    methods: {
      goRoute (routePath) {
        this.$router.push(routePath)
      },
      handleAvatarError (e) {
        // Prevent infinite loop - only set default if not already trying to load it
        if (e.target.src && !e.target.src.includes('default.png')) {
          e.target.src = '/public/avatar/default.png'
        } else {
          // If default.png also fails, use a data URI placeholder to stop the loop
          e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiNEOUQ5RDkiLz4KPHBhdGggZD0iTTE2IDEwQzE4LjIwOTEgMTAgMjAgMTEuNzkwOSAyMCAxNEMyMCAxNi4yMDkxIDE4LjIwOTEgMTggMTYgMThDMTMuNzkwOSAxOCAxMiAxNi4yMDkxIDEyIDE0QzEyIDExLjc5MDkgMTMuNzkwOSAxMCAxNiAxMFoiIGZpbGw9IiM5OTk5OTkiLz4KPHBhdGggZD0iTTE2IDIyQzE4LjY2NjcgMjIgMjEgMjAuNjY2NyAyMSAxOEgyMUMxOSAyMi4yMDkxIDE3LjIwOTEgMjQgMTUgMjRIMTdDMTQuMzMzMyAyNCAxMiAyMi42NjY3IDEyIDIwSDEyQzEyIDIyLjIwOTEgMTMuNzkwOSAyNCAxNiAyNFoiIGZpbGw9IiM5OTk5OTkiLz4KPC9zdmc+'
          e.target.onerror = null // Remove error handler to prevent further loops
        }
      }
    },
    computed: {
      ...mapGetters(['profile']),
      activeName () {
        return this.$route.path
      }
    }
  }
</script>

<style lang="less" scoped>
  @avatar-radius: 50%;

  .container {
    width: 90%;
    min-width: 800px;
    margin: auto;
  }

  .flex-container {
    .menu {
      flex: 1 0 150px;
      max-width: 250px;
      .avatar-editor {
        padding: 10% 22%;
        margin-bottom: 10px;
        .avatar-container {
          &:hover {
            .avatar-mask {
              opacity: .5;
            }
          }
          position: relative;
          .avatar {
            width: 100%;
            height: auto;
            max-width: 100%;
            display: block;
            border-radius: @avatar-radius;
            box-shadow: 0px 0px 1px 0px;
          }
          .avatar-mask {
            transition: opacity .2s ease-in;
            z-index: 1;
            border-radius: @avatar-radius;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: black;
            opacity: 0;
            .mask-content {
              position: absolute;
              top: 50%;
              left: 50%;
              z-index: 3;
              color: #fff;
              font-size: 16px;
              text-align: center;
              transform: translate(-50%, -50%);
              .text {
                white-space: nowrap;
              }
            }
          }
        }
      }

    }

    .panel {
      flex: auto;
      &::before {
        content: '';
        display: block;
        width: 1px;
        height: 100%;
        background: #dddee1;
        position: absolute;
        top: 0;
        bottom: 0;
        z-index: 1;
      }
    }

  }

  .ivu-menu-vertical.ivu-menu-light:after {
    /*Cancel default pseudo-element*/
    width: 0;
  }
</style>

<style lang="less">
  .setting-main {
    position: relative;
    margin: 10px 40px;
    padding-bottom: 20px;
    .setting-content {
      margin-left: 20px;
    }
    .mini-container {
      width: 500px;
    }
  }
</style>

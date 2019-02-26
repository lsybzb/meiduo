var vm = new Vue({
    el: '#app',
    data: {
        host: host,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        username: sessionStorage.username || localStorage.username,
        old_pwd: '',
        new_pwd: '',
        new_cpwd: '',
        error_opwd: false,
        error_pwd: false,
        error_cpwd: false
    },
    methods: {
        // 检查旧密码
        check_opwd: function(){
            if (!vm.old_pwd) {
                vm.error_opwd = true;
            } else {
                vm.error_opwd = false;
            }
        },
        // 检查新密码
        check_pwd: function(){
            len = vm.new_pwd.length;
            if (len<8 || len>20) {
                vm.error_pwd = true;
            } else {
                vm.error_pwd = false;
            }
        },
        // 检查确认密码
        check_cpwd: function(){
            if (vm.new_pwd != vm.new_cpwd) {
                vm.error_cpwd = true;
            } else {
                vm.error_cpwd = false;
            }
        },
        // 修改密码
        change_pwd: function(){
            if (vm.error_pwd || vm.error_cpwd ) {
                return;
            } 
            if (vm.user_id && vm.token) {
                axios.put(this.host + '/user/'+vm.user_id+'/password/',
                        {
                            old_password: vm.old_pwd,
                            password: vm.new_pwd,
                            password2: vm.new_cpwd
                        },
                        {
                            headers: {
                                'Authorization': 'JWT ' + vm.token
                            },
                            responseType: 'json'
                        } 
                    )
                    .then(function(response){
                        alert('密码修改成功');
                        location.href = "/user_center_info.html";
                    })
                    .catch(function(error){
                        if (error.status === 403) {
                            alert("403错误");
                            // location = '/index.html?next=/user_center_pass.html';
                        } else {
                            alert(error.data.message);
                        }
                    })
            } else {
                location.href = '/index.html?next=/user_center_pass.html';
            }
        },
        // 退出
        logout: function(){
            sessionStorage.clear();
            localStorage.clear();
            location.href = '/login.html';
        },
    }
})
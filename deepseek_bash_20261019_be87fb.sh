# 1. 进入你的项目目录 (将 /path/to/your/project 替换为你的实际路径)
cd C:\Users\yurou\Desktop\automations\Macro_Policy_Tracker


# 2. 初始化 Git 仓库，这会在当前目录生成一个隐藏的 .git 文件夹
git init

# 3. 将所有文件添加到暂存区 (注意有个英文句点 ".")
git add .

# 4. 提交这些文件，并附上描述信息
git commit -m "Initial commit: 项目首次提交"

# 5. 将本地仓库与你在 GitHub 上创建的远程仓库关联起来
# 将下面的 URL 替换为你刚刚复制的仓库地址
git remote add origin https://github.com/xuyuanzhang128-cloud/-.git

# 6. 将本地分支重命名为 main (GitHub 现在的默认分支名) 并推送
git branch -M main
git push -u origin main
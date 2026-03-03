load("config.js");
function execute(url, page) {
  if (!page) page = 1;
  url = url.replace("{{page}}", (page - 1) * 10);

  let response = fetch(url, {
    headers: {
      "User-Agent": UserAgent.android(),
    },
  });
  if (response.ok) {
    let json = response.json();
    let cmtList = json.data.comment;
    let comments = [];
    cmtList.forEach((cmt) => {
      let scoreCount = Math.round(cmt.score / 2);
      let score = "⭐".repeat(scoreCount) + "☆".repeat(5 - scoreCount);
      comments.push({
        name: cmt.user_info.user_name,
        content:
          score +
          "&nbsp;".repeat(24) +
          cmt.digg_count +
          "❤️  " +
          cmt.reply_count +
          "🗨️<br>" +
          cmt.text,
        description: formatChineseDate(cmt.create_timestamp),
      });
    });
    let next = parseInt(page, 10) + 1;
    return Response.success(comments, next.toString());
  }
  return null;
}

function formatChineseDate(timestamp) {
  const date = new Date(timestamp * 1000);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

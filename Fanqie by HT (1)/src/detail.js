load("config.js");
function execute(url) {
  const regex = /(?:[?&]book_id=|\/page\/)(\d+)(?=$|[?&\/#])/;
  let book_id = url.match(regex)[1];

  let res = fetch(url, {
    headers: {
      "User-Agent": UserAgent.android(),
    },
  });
  if (!res.ok) return null;
  let doc = res.html();

  let name = doc.select(".page-header-info h1").text();
  let cover = doc.select("img.page-header-img").attr("src");

  // Comment
  let comment = {
    input: `https://api5-normal-sinfonlinec.fqnovel.com/reading/ugc/novel_comment/book/v/?&book_id=${book_id}&aid=1967&offset={{page}}`,
    script: "comment.js",
  };

  // Script
  let script = doc.select("body > script:not([src])").first();
  let scriptText = script.html();
  var match = scriptText.match(/window\.__INITIAL_STATE__\s*=\s*({[\s\S]*?});/);
  if (!match) return null;
  var script_obj = JSON.parse(match[1]);

  // Suggestion
  const authorId = extractValueFromScript(script_obj, "authorId");
  let suggests = [
    {
      title: "同一作者",
      input: `https://api5-normal-sinfonlinec.fqnovel.com/reading/user/basic_info/get/v?user_id=${authorId}&aid=1967&version_code=65532`,
      script: "suggest.js",
    },
  ];

  // Detail
  const authorName = extractValueFromScript(script_obj, "authorName");
  const creationStatus =
    extractValueFromScript(script_obj, "creationStatus") == "1";
  const abstract = extractValueFromScript(script_obj, "abstract").replace(
    /\r?\n/g,
    "<br>",
  );

  // Info
  const chapterTotal = extractValueFromScript(script_obj, "chapterTotal");
  const lastChapterTitle = extractValueFromScript(
    script_obj,
    "lastChapterTitle",
  );
  const readCount = extractValueFromScript(script_obj, "readCount");
  const wordNumber = extractValueFromScript(script_obj, "wordNumber");
  const lastPublishTime = formatChineseDate(
    +extractValueFromScript(script_obj, "lastPublishTime"),
  );
  const description = extractValueFromScript(script_obj, "description");
  var score = "0";
  try {
    let scoreRes = fetch(
      "https://api5-normal-sinfonlinec.fqnovel.com/reading/user/share/info/v/?group_id=" +
        book_id +
        "&aid=1967&version_code=513",
    );
    if (scoreRes.ok) {
      let scoreJson = scoreRes.json();
      score = scoreJson.data.book_info.score;
    }
  } catch (e) {}

  // Category
  var categoryV2 = JSON.parse(extractValueFromScript(script_obj, "categoryV2"));
  var genres = [];
  categoryV2.forEach((e) => {
    genres.push({
      title: e.Name,
      input: hot_genres_url.replace("{{category_id}}", e.ObjectId),
      script: "gen.js",
    });
  });

  return Response.success({
    name: name,
    cover: cover,
    link: url,
    description: abstract,
    author: authorName,
    genres: genres,
    comment: comment,
    suggests: suggests,
    ongoing: creationStatus,
    detail:
      `描述: ${description}<br>` +
      `评价: ${score}/10<br>` +
      `章节号: ${chapterTotal}<br>` +
      `字数: ${wordNumber}<br>` +
      `浏览次数: ${readCount}<br>` +
      `更新: ${lastPublishTime}<br>` +
      `最新章节: ${lastChapterTitle}<br>`,
  });
}

function formatChineseDate(timestamp) {
  const date = new Date(timestamp * 1000);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}/${month}/${day} - ${hours}:${minutes}`;
}

function extractValueFromScript(obj, key) {
  function findValue(o) {
    if (!o || typeof o !== "object") return null;
    if (o[key] !== undefined) return o[key];
    for (var k in o) {
      var v = findValue(o[k]);
      if (v !== null) return v;
    }
    return null;
  }

  var value = findValue(obj);
  if (value === null || value === undefined) return null;
  return String(value);
}

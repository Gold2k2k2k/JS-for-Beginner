load("config.js");
function execute() {
  const category_url =
    "https://fanqienovel.com/api/author/book/category_list/v0/?gender=-1";
  let response = fetch(category_url);
  if (!response.ok) {
    return null;
  }

  let data = response.json().data;

  let hot_genres = [];
  data.forEach((e) => {
    hot_genres.push({
      title: e.name,
      input: hot_genres_url.replace("{{category_id}}", e.category_id),
      script: "gen.js",
    });
  });

  return Response.success(hot_genres);
}

import SwiftUI

/// The Naver News API doesn't provide thumbnail images or a 3-line summary,
/// only a title and short description (see app/services/news.py) — so we let
/// users open the original article link directly.
struct NewsListView: View {
    let state: LoadState<NewsResponse>

    var body: some View {
        CardContainer(title: "관련 뉴스", icon: "newspaper.fill") {
            CardStateView(state: state) { data in
                AnyView(
                    Group {
                        if data.articles.isEmpty {
                            Text("수집된 뉴스가 없습니다").font(.caption).foregroundStyle(.secondary)
                        } else {
                            VStack(alignment: .leading, spacing: 10) {
                                ForEach(data.articles) { article in
                                    Link(destination: URL(string: article.link) ?? URL(string: "https://naver.com")!) {
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(article.title).font(.subheadline.bold())
                                            Text(article.description)
                                                .font(.caption)
                                                .foregroundStyle(.secondary)
                                                .lineLimit(2)
                                            Text(article.publishedAt)
                                                .font(.caption2)
                                                .foregroundStyle(.tertiary)
                                        }
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                    }
                )
            }
        }
    }
}

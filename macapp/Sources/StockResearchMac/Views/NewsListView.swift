import SwiftUI

/// 네이버 뉴스 API는 썸네일 이미지나 3줄 요약을 안 주고 제목+짧은 설명만 준다
/// (app/services/news.py 참고) — 원문 링크로 바로 열 수 있게 한다.
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
